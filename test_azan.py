#!/usr/bin/env python3
"""
Test script for Solat Sync MY azan playback.
This script helps you test the azan service manually.

Usage:
1. Make sure your Home Assistant is running
2. Make sure you have configured a media player in the integration
3. Run this script with your Home Assistant details

Example:
python3 test_azan.py --host 192.168.1.100 --port 8123 --token YOUR_LONG_LIVED_TOKEN --prayer fajr --media_player media_player.living_room
"""

import argparse
import requests
import json
import sys

def test_azan_service(host, port, token, prayer, media_player, volume=0.7):
    """Test the azan service call."""
    url = f"http://{host}:{port}/api/services/solatsyncmy/play_azan"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    data = {
        "prayer": prayer,
        "media_player": media_player,
        "volume": volume
    }
    
    print(f"Testing azan playback for {prayer} prayer on {media_player}...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Azan service call successful!")
            print("Check your media player - the azan should be playing now.")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    
    return response.status_code == 200

def list_media_players(host, port, token):
    """List available media players."""
    url = f"http://{host}:{port}/api/states"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            states = response.json()
            media_players = [
                state for state in states 
                if state["entity_id"].startswith("media_player.")
            ]
            
            print("\n📻 Available Media Players:")
            for player in media_players:
                name = player["attributes"].get("friendly_name", player["entity_id"])
                state = player["state"]
                print(f"  - {player['entity_id']} ({name}) - {state}")
            
            return [player["entity_id"] for player in media_players]
        else:
            print(f"❌ Error listing media players: HTTP {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Test Solat Sync MY azan playback")
    parser.add_argument("--host", default="localhost", help="Home Assistant host")
    parser.add_argument("--port", default="8123", help="Home Assistant port")
    parser.add_argument("--token", required=True, help="Long-lived access token")
    parser.add_argument("--prayer", choices=["fajr", "dhuhr", "asr", "maghrib", "isha"], 
                       default="fajr", help="Prayer to test")
    parser.add_argument("--media_player", help="Media player entity ID")
    parser.add_argument("--volume", type=float, default=0.7, help="Volume (0.1-1.0)")
    parser.add_argument("--list-players", action="store_true", help="List available media players")
    
    args = parser.parse_args()
    
    print("🕌 Solat Sync MY Azan Test")
    print("=" * 40)
    
    if args.list_players:
        media_players = list_media_players(args.host, args.port, args.token)
        if not media_players:
            print("No media players found or error occurred.")
        return
    
    if not args.media_player:
        print("❌ Media player is required. Use --media_player or --list-players to see available players.")
        print("\nExample:")
        print(f"python3 {sys.argv[0]} --token YOUR_TOKEN --list-players")
        return
    
    success = test_azan_service(
        args.host, args.port, args.token, 
        args.prayer, args.media_player, args.volume
    )
    
    if success:
        print("\n🎵 If you can hear the azan, the integration is working correctly!")
        print("💡 You can now set up automations or use the switches in Home Assistant.")
    else:
        print("\n🔧 Troubleshooting tips:")
        print("1. Check that the integration is installed and configured")
        print("2. Verify your long-lived access token is correct")
        print("3. Make sure the media player exists and is available")
        print("4. Check Home Assistant logs for error messages")
        print("5. Ensure azan audio files are in the integration's audio/ directory")

if __name__ == "__main__":
    main() 