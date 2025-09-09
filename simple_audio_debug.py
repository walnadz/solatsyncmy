#!/usr/bin/env python3
"""
Simple Audio Debug Script for Solat Sync MY

This script checks if audio files are properly set up without requiring external dependencies.
"""

import os
import sys

def find_home_assistant_config():
    """Find Home Assistant configuration directory."""
    possible_paths = [
        os.path.expanduser("~/.homeassistant"),
        "/config",  # Docker/HAOS
        os.path.expanduser("~/homeassistant"),
        "/usr/share/hassio/homeassistant",
        # Add some Mac-specific paths
        os.path.expanduser("~/Library/Application Support/homeassistant"),
        "/Applications/Home Assistant.app/Contents/Resources/config",
    ]
    
    print("🔍 Looking for Home Assistant configuration...")
    for path in possible_paths:
        print(f"   Checking: {path}")
        if os.path.exists(os.path.join(path, "configuration.yaml")):
            print(f"✅ Found Home Assistant config at: {path}")
            return path
            
    print("❌ Could not find Home Assistant configuration directory")
    print("💡 Make sure Home Assistant is installed and has been run at least once")
    return None

def check_integration_files():
    """Check if integration files exist."""
    print("\n=== CHECKING INTEGRATION FILES ===")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    integration_path = os.path.join(current_dir, "custom_components", "solatsyncmy")
    
    if not os.path.exists(integration_path):
        print(f"❌ Integration not found at: {integration_path}")
        return False, None
        
    print(f"✅ Integration found at: {integration_path}")
    
    # Check audio directory
    audio_path = os.path.join(integration_path, "audio")
    if not os.path.exists(audio_path):
        print(f"❌ Audio directory not found: {audio_path}")
        return False, None
        
    print(f"✅ Audio directory found: {audio_path}")
    
    # Check audio files
    audio_files = ["azan.mp3", "azanfajr.mp3"]
    all_good = True
    
    for audio_file in audio_files:
        file_path = os.path.join(audio_path, audio_file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {audio_file}: {size:,} bytes")
        else:
            print(f"❌ {audio_file}: NOT FOUND")
            all_good = False
            
    return all_good, integration_path

def check_www_files(ha_config_path, integration_path):
    """Check if audio files are copied to www directory."""
    print("\n=== CHECKING WWW DIRECTORY ===")
    
    if not ha_config_path:
        print("❌ Cannot check www directory - Home Assistant config path not found")
        return False
        
    www_path = os.path.join(ha_config_path, "www", "solatsyncmy")
    print(f"WWW directory: {www_path}")
    
    if not os.path.exists(www_path):
        print("⚠️  WWW directory doesn't exist - this is normal if integration hasn't been loaded yet")
        return False
        
    # Check each audio file
    audio_files = ["azan.mp3", "azanfajr.mp3"]
    all_good = True
    
    for audio_file in audio_files:
        www_file = os.path.join(www_path, audio_file)
        if os.path.exists(www_file):
            size = os.path.getsize(www_file)
            print(f"✅ {audio_file}: {size:,} bytes in www")
        else:
            print(f"❌ {audio_file}: NOT FOUND in www")
            all_good = False
            
    return all_good

def copy_audio_files(ha_config_path, integration_path):
    """Copy audio files to www directory."""
    print("\n=== COPYING AUDIO FILES ===")
    
    if not ha_config_path or not integration_path:
        print("❌ Cannot copy files - missing paths")
        return False
        
    www_path = os.path.join(ha_config_path, "www", "solatsyncmy")
    
    try:
        os.makedirs(www_path, exist_ok=True)
        print(f"✅ Created/verified www directory: {www_path}")
    except Exception as e:
        print(f"❌ Failed to create www directory: {e}")
        return False
    
    # Copy files
    import shutil
    audio_files = ["azan.mp3", "azanfajr.mp3"]
    copied_any = False
    
    for audio_file in audio_files:
        source = os.path.join(integration_path, "audio", audio_file)
        dest = os.path.join(www_path, audio_file)
        
        if not os.path.exists(source):
            print(f"❌ Source file not found: {source}")
            continue
            
        try:
            if not os.path.exists(dest):
                shutil.copy2(source, dest)
                size = os.path.getsize(dest)
                print(f"✅ Copied {audio_file} ({size:,} bytes)")
                copied_any = True
            else:
                # Check if sizes match
                source_size = os.path.getsize(source)
                dest_size = os.path.getsize(dest)
                if source_size != dest_size:
                    shutil.copy2(source, dest)
                    print(f"✅ Updated {audio_file} ({dest_size:,} bytes)")
                    copied_any = True
                else:
                    print(f"✅ {audio_file} already exists and is current")
        except Exception as e:
            print(f"❌ Failed to copy {audio_file}: {e}")
    
    return copied_any

def generate_test_commands():
    """Generate test commands for Home Assistant."""
    print("\n=== SERVICE TEST COMMANDS ===")
    print("Copy these commands to Home Assistant Developer Tools > Services:")
    print()
    
    print("1. Test Audio Service:")
    print("service: solatsyncmy.test_audio")
    print("data:")
    print("  media_player: media_player.YOUR_PLAYER_NAME")
    print("  audio_file: azan.mp3")
    print("  volume: 0.5")
    print()
    
    print("2. Play Azan Service:")
    print("service: solatsyncmy.play_azan")
    print("data:")
    print("  prayer: dhuhr")
    print("  media_player: media_player.YOUR_PLAYER_NAME")
    print("  volume: 0.5")
    print()
    
    print("💡 Tips:")
    print("- Replace 'YOUR_PLAYER_NAME' with your actual media player entity ID")
    print("- Find media player entities in Developer Tools > States")
    print("- Look for entities starting with 'media_player.'")
    print("- Common examples: media_player.living_room_speaker, media_player.bedroom_tv")

def check_common_issues():
    """Check for common issues."""
    print("\n=== COMMON ISSUES TO CHECK ===")
    print("1. ✅ Make sure Home Assistant is running")
    print("2. ✅ Restart Home Assistant completely after installing the integration")
    print("3. ✅ Check that your media player supports MP3 files")
    print("4. ✅ Ensure your media player is turned on and accessible")
    print("5. ✅ Try accessing audio files directly:")
    print("   http://localhost:8123/local/solatsyncmy/azan.mp3")
    print("   http://localhost:8123/local/solatsyncmy/azanfajr.mp3")
    print("6. ✅ Check Home Assistant logs for any errors")
    print("7. ✅ Test with different media players if available")

def main():
    print("🔍 SOLAT SYNC MY - SIMPLE AUDIO DEBUG")
    print("=" * 50)
    
    # Step 1: Find Home Assistant config
    ha_config_path = find_home_assistant_config()
    
    # Step 2: Check integration files
    integration_ok, integration_path = check_integration_files()
    if not integration_ok:
        print("\n❌ Integration files are missing or incomplete")
        print("💡 Make sure you've downloaded the integration correctly")
        return
    
    # Step 3: Check www files
    www_ok = check_www_files(ha_config_path, integration_path)
    
    # Step 4: Copy files if needed and possible
    if not www_ok and ha_config_path:
        print("\n🔄 Audio files not found in www directory, attempting to copy...")
        copied = copy_audio_files(ha_config_path, integration_path)
        if copied:
            print("✅ Files copied successfully!")
            check_www_files(ha_config_path, integration_path)  # Check again
        else:
            print("⚠️  Could not copy files automatically")
    
    # Step 5: Generate test commands
    generate_test_commands()
    
    # Step 6: Common issues
    check_common_issues()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. If files were copied, restart Home Assistant completely")
    print("2. Test the service commands in Developer Tools > Services")
    print("3. Check Home Assistant logs for any errors during playback")
    print("4. If still not working, try a different media player")
    print()
    print("📝 Logs to check in Home Assistant:")
    print("   Settings > System > Logs")
    print("   Look for entries from 'custom_components.solatsyncmy'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDebug session cancelled by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc() 