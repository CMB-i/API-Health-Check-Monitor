# API Health Check Monitor

A lightweight, YAML-configured system that monitors REST API endpoints for
availability, response time, and response correctness — with a live terminal
dashboard, alert notifications, and persistent historical logging.

---

## Features

| Feature | Description |
|---|---|
| **Endpoint Monitoring** | Checks multiple APIs simultaneously using async HTTP |
| **Response Validation** | Verifies status codes, response structure, and field values |
| **Alert System** | Logs alerts and sends console/webhook notifications on failure |
| **Dashboard** | Live terminal UI showing uptime %, avg response time, status |
| **Historical Logging** | Stores every check result in SQLite for trend analysis |
| **YAML Config** | All endpoints, thresholds, and alert rules defined in one file |

---

## Monitored APIs (examples — all public, no auth required)

1. **JSONPlaceholder** — `https://jsonplaceholder.typicode.com/posts/1`
2. **Open-Meteo Weather** — `https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true`
3. **HTTPBin** — `https://httpbin.org/get`
4. **GitHub API** — `https://api.github.com`
5. **CoinGecko (ping)** — `https://api.coingecko.com/api/v3/ping`

---

## Quick Start

```bash
pip install -r requirements.txt
python monitor.py              # run once
python monitor.py --dashboard  # live terminal dashboard
python monitor.py --report     # print historical summary
