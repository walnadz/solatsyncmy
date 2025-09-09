#!/bin/bash

# Quick sync script for development - syncs files without restarting HA
# Usage: ./quick_sync.sh

set -e

HA_SERVER="nadzr@192.168.0.114"
HA_PATH="/ha/config/custom_components/solatsyncmy"
LOCAL_PATH="custom_components/solatsyncmy"

echo "⚡ Quick sync to Home Assistant server..."

# Sync only the component files (no audio to speed up)
echo "📂 Syncing Python files..."
scp $LOCAL_PATH/*.py $HA_SERVER:$HA_PATH/
scp $LOCAL_PATH/*.yaml $HA_SERVER:$HA_PATH/
scp $LOCAL_PATH/*.json $HA_SERVER:$HA_PATH/

echo "✅ Quick sync complete!"
echo "🔄 You may need to reload the integration or restart HA core for changes to take effect"
echo "💡 For full sync with restart, use: ./sync_to_ha.sh" 