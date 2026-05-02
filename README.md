# API Health Check Monitor

A modular, async CLI tool that monitors REST API endpoints for uptime, response time, and correctness — with live terminal output, desktop alerts, and persistent historical logging.

Built as a semester-end group project demonstrating real-world Python software architecture: async networking, database persistence, alerting, and CLI interfaces.

---

## Project Structure

```text
API-Health-Check-Monitor/
├── monitor.py              # Entry point — orchestrates all modules
├── config.yaml             # All settings and endpoint definitions
├── requirements.txt        # Python dependencies
│
├── core/
│   └── engine.py           # Async HTTP engine (Member 2)
│
├── data/
│   ├── logger.py           # SQLite persistence layer (Member 3)
│   └── health.db           # Auto-generated database
│
├── alerts/
│   ├── notifier.py         # Failure detection & notifications (Member 5)
│   └── failures.log        # Auto-generated alert log
│
└── ui/
    └── dashboard.py        # Live Rich terminal dashboard (Member 4)
```

---

## Features

| Feature | Description |
|---|---|
| Concurrent Monitoring | Checks all endpoints simultaneously using `asyncio` |
| Response Validation | Flags non-200 status codes and high latency |
| Desktop Alerts | Native notifications on macOS and Linux |
| Failure Logging | Persistent `failures.log` for every incident |
| Historical Logging | Every check stored in SQLite for trend analysis |
| Live Dashboard | Real-time terminal table via the `rich` library |
| YAML Configuration | All endpoints and thresholds in one config file |

---

## Monitored APIs

| # | Name | URL |
|---|---|---|
| 1 | JSONPlaceholder | `https://jsonplaceholder.typicode.com/posts/1` |
| 2 | GitHub API | `https://api.github.com` |
| 3 | HTTPBin | `https://httpbin.org/get` |
| 4 | Open-Meteo Weather | `https://api.open-meteo.com/v1/forecast?...` |
| 5 | CoinGecko Ping | `https://api.coingecko.com/api/v3/ping` |

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.10+ | Core language |
| `httpx` | Async HTTP requests |
| `asyncio` | Concurrent endpoint checks |
| `pyyaml` | YAML config parsing |
| `rich` | Terminal UI formatting |
| `sqlite3` | Historical data storage (built-in) |
| `logging` | Alert file logging (built-in) |

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/CMB-i/API-Health-Check-Monitor.git
cd API-Health-Check-Monitor

# 2. Install dependencies
pip install -r requirements.txt
```
---
## Usage
```
# Continuous monitoring (checks every 30s, press Ctrl+C to stop)
python monitor.py

# View historical report (last 20 checks + average latency)
python monitor.py --report
```
Example output:
```
API Health Monitor started. Press Ctrl+C to stop.

  JSONPlaceholder              UP    HTTP 200   143ms
  GitHub API                   UP    HTTP 200   228ms
  HTTPBin                      UP    HTTP 200   176ms
  Open-Meteo Weather           UP    HTTP 200   415ms
  CoinGecko Ping               UP    HTTP 200    91ms

Next check in 30s...
```
---
## Configuration (config.yaml)
```
settings:
  interval_seconds: 30       # How often to check (seconds)
  timeout_seconds: 5         # Per-request timeout
  latency_threshold_ms: 500  # Alert if response exceeds this

endpoints:
  - name: GitHub API
    url: https://api.github.com
  # Add more endpoints here...
```
To add a new endpoint, append a name + url entry under endpoints and restart the monitor.

---
## How It Works

```
config.yaml
    │
    ▼
monitor.py  ──►  core/engine.py      (async HTTP checks)
            ──►  data/logger.py      (save to SQLite)
            ──►  alerts/notifier.py  (alert on failure)
            ──►  ui/dashboard.py     (display results)
```
1. monitor.py loads config.yaml and initialises the database
2. core/engine.py pings all endpoints concurrently using asyncio.gather()
3. Results are saved to data/health.db via data/logger.py
4. alerts/notifier.py checks each result — fires a desktop notification and writes to failures.log if status ≠ 200 or latency exceeds the threshold
5. Results are rendered in the terminal; the loop sleeps for interval_seconds then repeats

---
## Team
| Member      | Role          | Deliverable                 |
| ----------- | ------------- | --------------------------- |
| Charvi      | Architect     | `monitor.py`, `config.yaml` |
| Mohana      | Network       | `core/engine.py`            |
| Pushpashree | Data          | `data/logger.py`            |
| Vaishnavi   | UI/UX         | `ui/dashboard.py`           |
| Lalith      | QA & DevOps   | `alerts/notifier.py`        |

