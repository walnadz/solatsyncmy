#!/usr/bin/env python3
"""Test script to debug audio playback issues with Solat Sync MY integration."""

import os
import urllib.request
import urllib.error
import json

def test_audio_files():
    """Test if audio files exist and are accessible."""
    print("🔍 Testing Audio Files...")
    
    # Check local files
    audio_dir = "custom_components/solatsyncmy/audio"
    if os.path.exists(audio_dir):
        print(f"✅ Audio directory exists: {audio_dir}")
        for file in os.listdir(audio_dir):
            if file.endswith('.mp3'):
                path = os.path.join(audio_dir, file)
                size = os.path.getsize(path)
                print(f"  📁 {file}: {size:,} bytes")
    else:
        print(f"❌ Audio directory not found: {audio_dir}")
    
    print()

def test_ha_www_access(ha_url="http://192.168.0.114:8123"):
    """Test if audio files are accessible via Home Assistant's www folder."""
    print("🌐 Testing Home Assistant WWW Access...")
    
    audio_files = ["azan.mp3", "azanfajr.mp3"]
    
    for audio_file in audio_files:
        url = f"{ha_url}/local/solatsyncmy/{audio_file}"
        print(f"  🔗 Testing: {url}")
        
        try:
            req = urllib.request.Request(url, method='HEAD')
            response = urllib.request.urlopen(req, timeout=10)
            content_length = response.headers.get('content-length', 'unknown')
            print(f"    ✅ Accessible - Size: {content_length} bytes")
        except urllib.error.HTTPError as e:
            print(f"    ❌ Not accessible - Status: {e.code}")
        except Exception as e:
            print(f"    ❌ Connection error: {e}")
    
    print()

def check_file_paths():
    """Check various file paths that might be used."""
    print("📂 Checking File Paths...")
    
    paths_to_check = [
        "custom_components/solatsyncmy/audio/azan.mp3",
        "custom_components/solatsyncmy/audio/azanfajr.mp3",
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✅ {path}: {size:,} bytes")
            
            # Check if file is readable
            try:
                with open(path, 'rb') as f:
                    # Read first few bytes to verify it's a valid file
                    header = f.read(10)
                    if header.startswith(b'ID3') or header[4:8] == b'ftyp':
                        print(f"    ✅ File appears to be valid audio")
                    else:
                        print(f"    ⚠️  File may not be valid audio (header: {header})")
            except Exception as e:
                print(f"    ❌ Cannot read file: {e}")
        else:
            print(f"  ❌ {path}: Not found")
    
    print()

def main():
    """Main test function."""
    print("🎵 Solat Sync MY Audio Debug Test")
    print("=" * 50)
    
    # Test 1: Local audio files
    test_audio_files()
    
    # Test 2: File paths
    check_file_paths()
    
    # Test 3: WWW access
    test_ha_www_access()
    
    print("🔧 Next Steps:")
    print("  1. Update to v1.0.6 if you haven't already")
    print("  2. Restart Home Assistant completely")
    print("  3. Check Home Assistant logs after testing the service:")
    print("     - Go to Settings → System → Logs")
    print("     - Filter for 'solatsyncmy'")
    print("  4. Try the service in Developer Tools with these exact values:")
    print("     Service: solatsyncmy.play_azan")
    print("     Data:")
    print("       prayer: fajr")
    print("       media_player: media_player.living_room_tv")
    print("       volume: 0.7")
    print("  5. If still no sound, try a different media player entity")

if __name__ == "__main__":
    main() 