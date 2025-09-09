#!/usr/bin/env python3
"""
Debug Audio Playback Script for Solat Sync MY

This script helps debug audio playback issues by testing:
1. Audio file existence and accessibility
2. Media player availability and state
3. Different URL formats and media types
4. Direct HTTP access to audio files

Run this script to identify why audio playback isn't working.
"""

import os
import sys
import asyncio
import aiohttp
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioPlaybackDebugger:
    def __init__(self):
        self.ha_config_path = None
        self.www_path = None
        self.integration_path = None
        self.audio_files = ["azan.mp3", "azanfajr.mp3"]
        
    def find_home_assistant_config(self):
        """Find Home Assistant configuration directory."""
        possible_paths = [
            os.path.expanduser("~/.homeassistant"),
            "/config",  # Docker/HAOS
            os.path.expanduser("~/homeassistant"),
            "/usr/share/hassio/homeassistant",
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "configuration.yaml")):
                self.ha_config_path = path
                self.www_path = os.path.join(path, "www", "solatsyncmy")
                logger.info(f"Found Home Assistant config at: {path}")
                return True
                
        logger.error("Could not find Home Assistant configuration directory")
        return False
    
    def check_integration_files(self):
        """Check if integration files exist."""
        logger.info("\n=== CHECKING INTEGRATION FILES ===")
        
        # Find integration path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        integration_path = os.path.join(current_dir, "custom_components", "solatsyncmy")
        
        if not os.path.exists(integration_path):
            logger.error(f"Integration not found at: {integration_path}")
            return False
            
        self.integration_path = integration_path
        audio_path = os.path.join(integration_path, "audio")
        
        logger.info(f"✅ Integration found at: {integration_path}")
        logger.info(f"Audio directory: {audio_path}")
        
        if not os.path.exists(audio_path):
            logger.error("❌ Audio directory not found!")
            return False
            
        # Check audio files
        for audio_file in self.audio_files:
            file_path = os.path.join(audio_path, audio_file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                logger.info(f"✅ {audio_file}: {size:,} bytes")
            else:
                logger.error(f"❌ {audio_file}: NOT FOUND")
                
        return True
    
    def check_www_files(self):
        """Check if audio files are copied to www directory."""
        logger.info("\n=== CHECKING WWW DIRECTORY ===")
        
        if not self.www_path:
            logger.error("❌ Home Assistant config path not found")
            return False
            
        logger.info(f"WWW directory: {self.www_path}")
        
        if not os.path.exists(self.www_path):
            logger.warning(f"⚠️  WWW directory doesn't exist: {self.www_path}")
            logger.info("This is expected if the integration hasn't been loaded yet")
            return False
            
        # Check each audio file
        all_good = True
        for audio_file in self.audio_files:
            www_file = os.path.join(self.www_path, audio_file)
            if os.path.exists(www_file):
                size = os.path.getsize(www_file)
                logger.info(f"✅ {audio_file}: {size:,} bytes in www")
            else:
                logger.error(f"❌ {audio_file}: NOT FOUND in www")
                all_good = False
                
        return all_good
    
    async def test_http_access(self):
        """Test HTTP access to audio files."""
        logger.info("\n=== TESTING HTTP ACCESS ===")
        
        if not self.www_path or not os.path.exists(self.www_path):
            logger.warning("⚠️  Skipping HTTP test - www directory not found")
            return
        
        base_urls = [
            "http://localhost:8123",
            "http://127.0.0.1:8123",
        ]
        
        async with aiohttp.ClientSession() as session:
            for audio_file in self.audio_files:
                logger.info(f"\nTesting HTTP access for: {audio_file}")
                
                for base_url in base_urls:
                    test_url = f"{base_url}/local/solatsyncmy/{audio_file}"
                    try:
                        async with session.head(test_url, timeout=5) as response:
                            if response.status == 200:
                                content_length = response.headers.get('content-length', 'unknown')
                                content_type = response.headers.get('content-type', 'unknown')
                                logger.info(f"✅ {test_url}")
                                logger.info(f"   Content-Length: {content_length}")
                                logger.info(f"   Content-Type: {content_type}")
                            else:
                                logger.warning(f"⚠️  {test_url} - Status: {response.status}")
                    except asyncio.TimeoutError:
                        logger.warning(f"⏱️  {test_url} - Timeout")
                    except Exception as e:
                        logger.warning(f"❌ {test_url} - Error: {e}")
    
    def copy_missing_files(self):
        """Copy audio files to www directory if missing."""
        logger.info("\n=== COPYING AUDIO FILES ===")
        
        if not self.ha_config_path:
            logger.error("❌ Cannot copy files - Home Assistant config path not found")
            return False
            
        if not self.integration_path:
            logger.error("❌ Cannot copy files - Integration path not found")
            return False
            
        # Create www directory
        try:
            os.makedirs(self.www_path, exist_ok=True)
            logger.info(f"✅ Created/verified www directory: {self.www_path}")
        except Exception as e:
            logger.error(f"❌ Failed to create www directory: {e}")
            return False
        
        # Copy files
        import shutil
        copied_any = False
        
        for audio_file in self.audio_files:
            source = os.path.join(self.integration_path, "audio", audio_file)
            dest = os.path.join(self.www_path, audio_file)
            
            if not os.path.exists(source):
                logger.error(f"❌ Source file not found: {source}")
                continue
                
            try:
                if not os.path.exists(dest):
                    shutil.copy2(source, dest)
                    size = os.path.getsize(dest)
                    logger.info(f"✅ Copied {audio_file} ({size:,} bytes)")
                    copied_any = True
                else:
                    # Check if sizes match
                    source_size = os.path.getsize(source)
                    dest_size = os.path.getsize(dest)
                    if source_size != dest_size:
                        shutil.copy2(source, dest)
                        logger.info(f"✅ Updated {audio_file} ({dest_size:,} bytes)")
                        copied_any = True
                    else:
                        logger.info(f"✅ {audio_file} already exists and is current")
            except Exception as e:
                logger.error(f"❌ Failed to copy {audio_file}: {e}")
        
        return copied_any
    
    def generate_service_test_commands(self):
        """Generate Home Assistant service test commands."""
        logger.info("\n=== SERVICE TEST COMMANDS ===")
        logger.info("Copy these commands to Home Assistant Developer Tools > Services:")
        logger.info("")
        
        # Test audio service
        logger.info("1. Test Audio Service:")
        logger.info("service: solatsyncmy.test_audio")
        logger.info("data:")
        logger.info("  media_player: media_player.YOUR_PLAYER_NAME")
        logger.info("  audio_file: azan.mp3")
        logger.info("  volume: 0.5")
        logger.info("")
        
        # Play azan service
        logger.info("2. Play Azan Service:")
        logger.info("service: solatsyncmy.play_azan")
        logger.info("data:")
        logger.info("  prayer: dhuhr")
        logger.info("  media_player: media_player.YOUR_PLAYER_NAME")
        logger.info("  volume: 0.5")
        logger.info("")
        
        logger.info("Replace 'YOUR_PLAYER_NAME' with your actual media player entity ID")
        logger.info("You can find media player entities in Developer Tools > States")
    
    def check_common_issues(self):
        """Check for common issues that prevent audio playback."""
        logger.info("\n=== CHECKING COMMON ISSUES ===")
        
        issues_found = []
        
        # Check if Home Assistant is running
        try:
            import requests
            response = requests.get("http://localhost:8123", timeout=5)
            logger.info("✅ Home Assistant is responding")
        except Exception:
            issues_found.append("❌ Home Assistant might not be running or accessible")
        
        # Check if www directory is accessible
        if self.www_path and os.path.exists(self.www_path):
            # Check permissions
            if not os.access(self.www_path, os.R_OK):
                issues_found.append(f"❌ WWW directory not readable: {self.www_path}")
        
        # Check for file size issues
        if self.www_path and os.path.exists(self.www_path):
            for audio_file in self.audio_files:
                file_path = os.path.join(self.www_path, audio_file)
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    if size == 0:
                        issues_found.append(f"❌ {audio_file} is empty (0 bytes)")
                    elif size < 1000:  # Less than 1KB is suspicious
                        issues_found.append(f"⚠️  {audio_file} is very small ({size} bytes)")
        
        if issues_found:
            logger.info("Issues found:")
            for issue in issues_found:
                logger.info(f"  {issue}")
        else:
            logger.info("✅ No obvious issues detected")
    
    async def run_full_debug(self):
        """Run complete debugging sequence."""
        logger.info("🔍 SOLAT SYNC MY - AUDIO PLAYBACK DEBUGGER")
        logger.info("=" * 50)
        
        # Step 1: Find Home Assistant
        if not self.find_home_assistant_config():
            logger.error("Cannot continue without Home Assistant config directory")
            return
        
        # Step 2: Check integration files
        if not self.check_integration_files():
            logger.error("Integration files are missing or incomplete")
            return
        
        # Step 3: Check www files
        www_exists = self.check_www_files()
        
        # Step 4: Copy files if needed
        if not www_exists:
            logger.info("Audio files not found in www directory, attempting to copy...")
            self.copy_missing_files()
            self.check_www_files()  # Check again
        
        # Step 5: Test HTTP access
        await self.test_http_access()
        
        # Step 6: Check common issues
        self.check_common_issues()
        
        # Step 7: Generate test commands
        self.generate_service_test_commands()
        
        logger.info("\n" + "=" * 50)
        logger.info("🎯 NEXT STEPS:")
        logger.info("1. Restart Home Assistant if you made any changes")
        logger.info("2. Test the service commands in Developer Tools > Services")
        logger.info("3. Check Home Assistant logs for any errors")
        logger.info("4. If still not working, check your media player compatibility")

async def main():
    debugger = AudioPlaybackDebugger()
    await debugger.run_full_debug()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDebug session cancelled by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc() 