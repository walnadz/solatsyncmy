#!/bin/bash

# Sync script to deploy SolatSync MY to Home Assistant server
# Usage: ./sync_to_ha.sh [commit_message]

set -e

HA_SERVER="nadzr@192.168.0.114"
HA_PATH="/ha/config/custom_components/solatsyncmy"
LOCAL_PATH="custom_components/solatsyncmy"

echo "🚀 Starting SolatSync MY deployment..."

# Check if local changes exist
if git diff --quiet; then
    echo "✅ No local changes detected"
else
    echo "📝 Local changes detected"
    git status --short
    
    # If commit message provided, commit changes
    if [ "$1" ]; then
        echo "📦 Committing changes: $1"
        git add .
        git commit -m "$1"
        git push origin main
        echo "✅ Changes committed and pushed to GitHub"
    else
        echo "⚠️  Warning: Local changes not committed (provide commit message to auto-commit)"
    fi
fi

echo "📂 Syncing files to Home Assistant server..."

# Sync the component files
scp -r $LOCAL_PATH/* $HA_SERVER:$HA_PATH/

echo "🔄 Restarting Home Assistant..."

# Restart Home Assistant
ssh $HA_SERVER "sudo systemctl restart home-assistant@homeassistant"

echo "✅ Deployment complete!"
echo "🏠 Home Assistant should be restarting now"
echo "📱 Check your HA instance in about 30-60 seconds"

# Optional: Check HA status
echo "⏱️  Waiting 30 seconds before checking status..."
sleep 30

ssh $HA_SERVER "sudo systemctl status home-assistant@homeassistant --no-pager -l | head -20"

echo ""
echo "🎉 Sync complete! Your changes are now live on Home Assistant."
echo "📖 To make further changes:"
echo "   1. Edit files locally"
echo "   2. Run: ./sync_to_ha.sh 'Your commit message'"
echo "   3. Test on your HA instance" 