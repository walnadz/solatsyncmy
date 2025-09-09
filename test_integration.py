#!/usr/bin/env python3
"""
Test script for Solat Sync MY integration services.
Run this to check if all services are working properly.
"""

import requests
import json
import sys
import os

# Home Assistant configuration
HA_URL = "http://192.168.0.114:8123"  # Update this to your Home Assistant URL
HA_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN"  # Update this with your token

def test_service_call(service_name, service_data=None):
    """Test calling a Home Assistant service."""
    url = f"{HA_URL}/api/services/solatsyncmy/{service_name}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = service_data or {}
    
    print(f"\n🧪 Testing service: solatsyncmy.{service_name}")
    print(f"📡 URL: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Service call successful!")
            return True
        else:
            print(f"❌ Service call failed!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def get_media_players():
    """Get list of available media players."""
    url = f"{HA_URL}/api/states"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            states = response.json()
            media_players = [
                entity["entity_id"] 
                for entity in states 
                if entity["entity_id"].startswith("media_player.")
            ]
            return media_players
        else:
            print(f"❌ Failed to get states: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting media players: {e}")
        return []

def main():
    """Main test function."""
    print("🕌 Solat Sync MY Integration Test")
    print("=" * 50)
    
    # Check if token is configured
    if HA_TOKEN == "YOUR_LONG_LIVED_ACCESS_TOKEN":
        print("❌ Please update the HA_TOKEN variable with your Home Assistant long-lived access token")
        print("🔗 Get your token from: Home Assistant > Profile > Long-lived access tokens")
        return
    
    # Get available media players
    print("🔍 Finding media players...")
    media_players = get_media_players()
    
    if not media_players:
        print("❌ No media players found. Please add a media player to Home Assistant first.")
        return
    
    print(f"📻 Found {len(media_players)} media player(s):")
    for i, player in enumerate(media_players, 1):
        print(f"   {i}. {player}")
    
    # Use first media player for testing
    test_media_player = media_players[0]
    print(f"🎯 Using {test_media_player} for testing")
    
    # Test 1: Refresh prayer times service
    print("\n" + "="*50)
    test_service_call("refresh_prayer_times")
    
    # Test 2: Test audio service
    print("\n" + "="*50)
    test_service_call("test_audio", {
        "media_player": test_media_player,
        "audio_file": "azan.mp3",
        "volume": 0.3
    })
    
    # Test 3: Play azan service
    print("\n" + "="*50)
    test_service_call("play_azan", {
        "prayer": "dhuhr",
        "media_player": test_media_player,
        "volume": 0.3
    })
    
    print("\n" + "="*50)
    print("✅ Test completed!")
    print("📋 Check your Home Assistant logs for detailed service execution info")
    print("🔗 Logs: Home Assistant > Settings > System > Logs")

if __name__ == "__main__":
    main() 