# Start Here - Quick Setup Guide

## If you just pulled the latest code from GitHub:

### 1. Navigate to the project directory
```bash
cd /Users/digantjain/Documents/GitHub/lululemon_alerts
```

### 2. Set up Python environment (if not already done)
```bash
# Create virtual environment (if it doesn't exist)
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure email (if not already done)
Edit `config.json` and make sure your email settings are correct:
- `from`: Your Gmail address
- `to`: Recipient email address  
- `password`: Your Gmail App Password

### 4. Set up LaunchAgent (automatic background running)
```bash
# Make script executable
chmod +x setup_launchagent.sh

# Run setup
./setup_launchagent.sh

# Start the monitor
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

### 5. Verify it's running
```bash
# Check status
launchctl list | grep lululemon

# View logs (optional)
tail -f monitor.log
```

## That's it! 

The monitor will now:
- ✅ Run automatically in the background
- ✅ Check all 29 products every 30 minutes
- ✅ Send email alerts when products are in stock at the right price
- ✅ Start automatically when you log in

## Quick Test (Optional)

To test manually once:
```bash
cd /Users/digantjain/Documents/GitHub/lululemon_alerts
source venv/bin/activate
python monitor.py --run-once
```

## Need Help?

- **View logs**: `tail -f monitor.log`
- **Check if running**: `launchctl list | grep lululemon`
- **Stop monitor**: `launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist`
- **Start monitor**: `launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist`

See `QUICK_COMMANDS.md` for all commands.
