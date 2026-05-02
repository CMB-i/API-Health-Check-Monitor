import asyncio
import sys
import yaml
from pathlib import Path
from rich.console import Console

from core.engine import check_all_endpoints
from data.logger import init_db, safe_log_results, get_recent_logs, get_avg_latency
from alerts.notifier import process_alerts

console = Console()
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def map_for_alerts(results):
    # engine uses 'status_code'/'latency_ms'; notifier expects 'status'/'latency'
    return [
        {"name": r["name"], "status": r["status_code"], "latency": r["latency_ms"]}
        for r in results
    ]


async def run_cycle(endpoints, timeout, latency_threshold_ms):
    results = list(await check_all_endpoints(endpoints, timeout=timeout))
    safe_log_results(results)
    process_alerts(map_for_alerts(results), latency_threshold_ms=latency_threshold_ms)
    return results


def print_results(results):
    # Inline display used until ui/dashboard.py (Member 4) is integrated
    console.print()
    for r in results:
        health = "[bold green]UP[/bold green]" if r["is_up"] else "[bold red]DOWN[/bold red]"
        status = str(r["status_code"]) if r["status_code"] else "ERR"
        error = f"  [dim]{r['error']}[/dim]" if r["error"] else ""
        console.print(f"  {r['name']:<28} {health}  HTTP {status:<5}  {r['latency_ms']:.0f}ms{error}")
    console.print()


def print_report():
    logs = get_recent_logs(limit=20)
    avg = get_avg_latency()

    console.rule("[bold cyan]Historical Report (last 20 checks)[/bold cyan]")
    for name, status_code, latency_ms, timestamp in logs:
        console.print(f"  {timestamp}  {name:<28}  HTTP {status_code or 'ERR'}  {latency_ms:.0f}ms")

    if avg is not None:
        console.print(f"\n[bold]Average latency:[/bold] [cyan]{avg:.1f}ms[/cyan]")
    else:
        console.print("\n[dim]No data yet — run the monitor first.[/dim]")


async def run_loop(config):
    settings = config.get("settings", {})
    endpoints = config["endpoints"]
    interval = settings.get("interval_seconds", 30)
    timeout = settings.get("timeout_seconds", 5)
    latency_threshold = settings.get("latency_threshold_ms", 500)

    console.print("[bold cyan]API Health Monitor started.[/bold cyan] Press Ctrl+C to stop.")

    while True:
        results = await run_cycle(endpoints, timeout, latency_threshold)
        print_results(results)
        console.print(f"[dim]Next check in {interval}s...[/dim]")
        await asyncio.sleep(interval)


def main():
    config = load_config()
    init_db()

    if "--report" in sys.argv:
        print_report()
    else:
        try:
            asyncio.run(run_loop(config))
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Monitor stopped.[/bold yellow]")


if __name__ == "__main__":
    main()
