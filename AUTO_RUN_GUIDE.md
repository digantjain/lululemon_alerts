# How to Run the Monitor Automatically Behind the Scenes

There are several ways to run the Lululemon monitor automatically in the background. Here are your options, ranked by recommendation:

## 🏆 Option 1: LaunchAgent (RECOMMENDED for macOS)

**Best for**: Running continuously in the background, auto-starting on login, and automatic restart if it crashes.

### Quick Setup

1. **Run the setup script** (easiest):
   ```bash
   ./setup_launchagent.sh
   ```

2. **Start the monitor**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
   ```

3. **That's it!** It will:
   - ✅ Start running immediately
   - ✅ Run continuously in the background
   - ✅ Automatically start when you log in
   - ✅ Restart automatically if it crashes
   - ✅ Log to `monitor.log` and `monitor.error.log`

### Managing the Service

**Check if it's running**:
```bash
launchctl list | grep lululemon
```

**Stop the monitor**:
```bash
launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

**Restart the monitor**:
```bash
launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

**View live logs**:
```bash
tail -f monitor.log              # Normal output
tail -f monitor.error.log        # Error output
```

### What Happens Behind the Scenes

1. **LaunchAgent** is macOS's built-in service manager
2. It runs your Python script as a background process
3. The script runs continuously, checking products every 15 minutes (configurable)
4. It keeps running even if:
   - You close the Terminal
   - You log out and log back in
   - The Mac restarts
   - The process crashes (it auto-restarts)

---

## Option 2: Background Process with nohup

**Best for**: Quick testing or if you just want it running until you restart your Mac.

### Setup

```bash
cd /Users/digantjain/Documents/GitHub/lululemon_alerts
source venv/bin/activate
nohup python monitor.py > monitor.log 2>&1 &
```

### Check if it's running

```bash
ps aux | grep monitor.py
```

### Stop it

```bash
pkill -f monitor.py
```

**Note**: This will stop running if you restart your Mac. Use LaunchAgent for permanent background running.

---

## Option 3: Cron Job (Periodic Checks)

**Best for**: Running checks periodically without a continuously running process.

### Setup

1. **Edit your crontab**:
   ```bash
   crontab -e
   ```

2. **Add this line** (checks every 15 minutes):
   ```
   */15 * * * * cd /Users/digantjain/Documents/GitHub/lululemon_alerts && /Users/digantjain/Documents/GitHub/lululemon_alerts/venv/bin/python monitor.py --run-once
   ```

3. **Save and exit**

**Note**: This runs a single check every 15 minutes instead of continuously. The monitor supports `--run-once` mode for this.

---

## Option 4: Screen/Tmux Session

**Best for**: Development/testing where you want to easily see output or stop/start manually.

### Setup with Screen

1. **Start a screen session**:
   ```bash
   screen -S lululemon
   ```

2. **Run the monitor**:
   ```bash
   python monitor.py
   ```

3. **Detach** (keeps running): Press `Ctrl+A` then `D`

4. **Reattach later**:
   ```bash
   screen -r lululemon
   ```

5. **Stop**: Reattach and press `Ctrl+C`

**Note**: This requires the terminal/screen session to stay active.

---

## 🎯 Recommended: LaunchAgent

For most users, **LaunchAgent (Option 1)** is the best choice because:

1. ✅ **Truly automatic** - Runs without any user interaction
2. ✅ **Persistent** - Survives restarts and logouts
3. ✅ **Reliable** - Auto-restarts if it crashes
4. ✅ **Low maintenance** - Set it once and forget it
5. ✅ **Native macOS** - Uses built-in system services

## How It Works (LaunchAgent)

When you use LaunchAgent:

1. **On Login**: macOS automatically loads the LaunchAgent and starts your monitor
2. **Background Process**: The monitor runs as a background daemon, completely invisible
3. **Continuous Monitoring**: It checks all 30 products every 15 minutes
4. **Email Alerts**: When a product meets your criteria, it sends an email automatically
5. **State Tracking**: It remembers which products it's already alerted you about
6. **Logging**: All activity is logged to files you can check anytime

## Verifying It's Working

After setting up LaunchAgent, verify it's working:

1. **Check status**:
   ```bash
   launchctl list | grep lululemon
   ```
   Should show the service is loaded and running.

2. **Check logs**:
   ```bash
   tail -20 monitor.log
   ```
   Should show recent check activity with timestamps.

3. **Wait 15 minutes** and check again to see if it's checking products.

## Troubleshooting

**Monitor not running?**
```bash
# Check if loaded
launchctl list | grep lululemon

# Check logs for errors
cat monitor.error.log

# Try restarting
launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

**Not receiving emails?**
- Check that email settings in `config.json` are correct
- Verify Gmail App Password is set correctly
- Check `monitor.error.log` for email errors

**Want to change check interval?**
- Edit `config.json` and change `check_interval_minutes`
- Restart the LaunchAgent

---

## Summary

**For automatic, hands-off monitoring**: Use **LaunchAgent (Option 1)**

Just run:
```bash
./setup_launchagent.sh
launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist
```

Then it will run continuously in the background, checking your 30 products every 15 minutes and sending you email alerts when products come in stock at the right price! 🎉
