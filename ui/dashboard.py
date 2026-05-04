from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich import box
import asyncio

console = Console()


def create_dashboard_table(results):
    table = Table(
        title="🚀 API Health Monitor",
        box=box.ROUNDED,
        expand=True
    )

    table.add_column("API Name", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("HTTP Code", justify="center")
    table.add_column("Latency (ms)", justify="center")
    table.add_column("Error", style="red")

    for r in results:
        is_up = r.get("is_up", False)

        status = "✅ UP" if is_up else "❌ DOWN"
        status_color = "green" if is_up else "red"

        latency = r.get("latency_ms", 0)

        table.add_row(
            r.get("name", "N/A"),
            f"[{status_color}]{status}[/{status_color}]",
            str(r.get("status_code")),
            f"{latency:.2f}",
            str(r.get("error")) if r.get("error") else "-"
        )

    return table


async def dashboard_loop(results_provider, interval=5):
    """
    results_provider: async function that returns results list
    interval: refresh time in seconds
    """

    with Live(console=console, refresh_per_second=2) as live:
        while True:
            try:
                results = await results_provider()
                table = create_dashboard_table(results)
                live.update(table)
            except Exception as e:
                error_table = Table(title="Dashboard Error", box=box.ROUNDED)
                error_table.add_column("Error")
                error_table.add_row(str(e))
                live.update(error_table)

            await asyncio.sleep(interval)
