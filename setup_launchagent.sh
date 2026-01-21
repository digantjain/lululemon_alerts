#!/bin/bash
# Setup script to create LaunchAgent for automatic monitoring

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
MONITOR_SCRIPT="$SCRIPT_DIR/monitor.py"
PLIST_FILE="$HOME/Library/LaunchAgents/com.lululemon.monitor.plist"

echo "Setting up LaunchAgent for Lululemon Monitor..."
echo "Script directory: $SCRIPT_DIR"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create the plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lululemon.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$MONITOR_SCRIPT</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/monitor.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/monitor.error.log</string>
</dict>
</plist>
EOF

echo "✓ LaunchAgent plist created: $PLIST_FILE"
echo ""
echo "To start the monitor, run:"
echo "  launchctl load ~/Library/LaunchAgents/com.lululemon.monitor.plist"
echo ""
echo "To stop the monitor, run:"
echo "  launchctl unload ~/Library/LaunchAgents/com.lululemon.monitor.plist"
echo ""
echo "To check status:"
echo "  launchctl list | grep lululemon"
echo ""
echo "To view logs:"
echo "  tail -f $SCRIPT_DIR/monitor.log"
echo "  tail -f $SCRIPT_DIR/monitor.error.log"
