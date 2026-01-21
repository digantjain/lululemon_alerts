# Lululemon Product Monitor

Automatically monitors Lululemon products for stock availability and price alerts. Sends email notifications when products come in stock at your specified price threshold.

## Features

- Monitors 29 product URLs simultaneously
- Checks stock availability and price every 30 minutes
- Sends email notifications when products meet your criteria (in stock + price under threshold)
- Tracks state to avoid duplicate alerts
- Runs automatically in the background on your Mac

## Two-Tier Alert System

### S1 - Best Deal (< $50)
- **Email Subject**: "Best lululemon deal"
- **Trigger**: Product becomes in stock at < $50 AND wasn't in S1 before

### S2 - Great Deal ($50-$60)
- **Email Subject**: "Great lululemon deal"
- **Trigger**: Product becomes in stock at $50-$60 AND wasn't in S1 or S2 before

## Setup

### 1. Install Dependencies

```bash
cd /Users/digantjain/Documents/GitHub/lululemon_alerts
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Email

Your email settings are already configured in `config.json`. The monitor uses Gmail with an App Password.

### 3. Set Up LaunchAgent (Automatic Background Running)

Run the setup script:

```bash
./setup_launchagent.sh
```

This creates a LaunchAgent that will:
- Run the monitor automatically in the background
- Start automatically when you log in
- Restart automatically if it crashes

### 4. Start the Monitor

```bash
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

That's it! The monitor will now run automatically.

## Managing the Monitor

**Check if it's running:**
```bash
launchctl list | grep lululemon
```

**Stop the monitor:**
```bash
launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

**Restart the monitor:**
```bash
launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

**View live logs:**
```bash
tail -f monitor.log              # Normal output
tail -f monitor.error.log        # Error output
```

## Manual Testing

To test the monitor manually:

```bash
python monitor.py --run-once
```

## Files

- `monitor.py` - Main monitoring script
- `config.json` - Configuration (email, products, etc.)
- `urls.json` - Product URLs (29 products)
- `requirements.txt` - Python dependencies
- `setup_launchagent.sh` - Setup script for automatic running

## Troubleshooting

**Not receiving emails?**
- Check that your Gmail App Password is correct in `config.json`
- Check `monitor.error.log` for email errors

**Monitor not running?**
- Check status: `launchctl list | grep lululemon`
- Check logs: `tail -f monitor.log` and `tail -f monitor.error.log`
- Try restarting: unload then load the LaunchAgent

**Products not detected?**
- The monitor uses multiple detection strategies
- Check logs to see what's being detected
- Enable debug mode in `config.json` by setting `"debug": true`

## Notes

- The monitor runs every 30 minutes automatically
- State is tracked in `monitor_state.json` to prevent duplicate alerts
- Logs are written to `monitor.log` and `monitor.error.log`
