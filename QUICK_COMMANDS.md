# Quick Commands Reference

All commands should be run in **Terminal** (macOS).

## Opening Terminal

1. Press `Cmd + Space` to open Spotlight
2. Type "Terminal" and press Enter
3. Or go to Applications → Utilities → Terminal

## Navigate to Project Directory

First, navigate to the project directory:

```bash
cd /Users/digantjain/Documents/GitHub/lululemon_alerts
```

## View Logs

### See what the monitor is doing:
```bash
tail -f monitor.log
```

### See any errors:
```bash
tail -f monitor.error.log
```

**Note**: These commands will show live updates. Press `Ctrl+C` to stop viewing.

## Control the Monitor

### Check if it's running:
```bash
launchctl list | grep lululemon
```

### Stop the monitor:
```bash
launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

### Start the monitor:
```bash
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

### Restart the monitor:
```bash
launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

## Manual Test Run

To test the monitor manually (runs once and exits):

```bash
cd /Users/digantjain/Documents/GitHub/lululemon_alerts
source venv/bin/activate
python monitor.py --run-once
```

## Quick Status Check

To quickly see if it's running and view recent activity:

```bash
# Check if running
launchctl list | grep lululemon

# View last 20 lines of log
tail -20 monitor.log
```
