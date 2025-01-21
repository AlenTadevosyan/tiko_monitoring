# Hyperliquid Monitor

A monitoring system for tracking Hyperliquid transactions.

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Configure settings in `config/settings.yaml`:
- Update addresses to monitor
- Adjust monitoring intervals
- Configure alert settings

## Usage

Run the monitor:
```bash
python -m src.main
```

## Structure

```
hyperliquid_monitor/
├── README.md
├── requirements.txt
├── config/
│   ├── config.py          # Configuration management
│   └── settings.yaml      # Config values
├── src/
│   ├── main.py           # Entry point
│   ├── client.py         # Hyperliquid API client
│   ├── monitor.py        # Main monitoring logic
│   ├── alerts/           # Alert system
│   └── utils/            # Utilities
└── tests/                # Test files
``` 