#!/usr/bin/env python3
"""
Test Local Audio Setup for Solat Sync MY

This script tests the local audio file setup by:
1. Checking if the /config/www/solatsyncmy/ directory exists
2. Verifying audio files are present and accessible
3. Testing HTTP access to the files
4. Providing setup guidance if issues are found

Usage:
    python tools/test_local_audio.py
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

class LocalAudioTester:
    def __init__(self):
        self.ha_config_path = None
        self.www_audio_path = None
        self.expected_files = ["azan.mp3", "azanfajr.mp3"]
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        
    def find_ha_config(self):
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
                self.www_audio_path = os.path.join(path, "www", "solatsyncmy")
                logger.info(f"✅ Found Home Assistant config at: {path}")
                return True
                
        logger.error("❌ Could not find Home Assistant configuration directory")
        return False
    
    def check_directory_structure(self):
        """Check if the required directory structure exists."""
        logger.info("\n=== CHECKING DIRECTORY STRUCTURE ===")
        
        if not self.ha_config_path:
            logger.error("❌ Home Assistant config path not found")
            return False
            
        www_path = os.path.join(self.ha_config_path, "www")
        
        if not os.path.exists(www_path):
            logger.error(f"❌ WWW directory doesn't exist: {www_path}")
            logger.info("💡 Create it with: mkdir -p /config/www")
            return False
        else:
            logger.info(f"✅ WWW directory exists: {www_path}")
            
        if not os.path.exists(self.www_audio_path):
            logger.warning(f"⚠️  Audio directory doesn't exist: {self.www_audio_path}")
            logger.info("💡 Create it with: mkdir -p /config/www/solatsyncmy")
            logger.info("   This is normal if the integration hasn't been loaded yet")
            return False
        else:
            logger.info(f"✅ Audio directory exists: {self.www_audio_path}")
            
        return True
    
    def check_audio_files(self):
        """Check for audio files in the directory."""
        logger.info("\n=== CHECKING AUDIO FILES ===")
        
        if not os.path.exists(self.www_audio_path):
            logger.error("❌ Audio directory not found")
            return False
            
        # Get all audio files
        audio_files = []
        for file in os.listdir(self.www_audio_path):
            file_path = os.path.join(self.www_audio_path, file)
            if any(file.lower().endswith(ext) for ext in self.supported_formats):
                if os.path.getsize(file_path) > 1024:  # > 1KB
                    audio_files.append(file)
                else:
                    logger.warning(f"⚠️  {file}: File too small ({os.path.getsize(file_path)} bytes) - likely a placeholder")
        
        if not audio_files:
            logger.error("❌ No valid audio files found")
            logger.info("💡 Expected files: azan.mp3, azanfajr.mp3")
            logger.info("💡 Supported formats: MP3, WAV, M4A, OGG, FLAC")
            return False
            
        logger.info(f"✅ Found {len(audio_files)} audio file(s):")
        for file in sorted(audio_files):
            file_path = os.path.join(self.www_audio_path, file)
            size_kb = os.path.getsize(file_path) // 1024
            logger.info(f"   • {file} ({size_kb} KB)")
            
        # Check for expected files
        found_expected = []
        for expected in self.expected_files:
            if expected in audio_files:
                found_expected.append(expected)
                
        if found_expected:
            logger.info(f"✅ Standard files found: {', '.join(found_expected)}")
        else:
            logger.warning("⚠️  No standard files (azan.mp3, azanfajr.mp3) found")
            logger.info("💡 Prayer-specific files can also be used")
            
        return True
    
    async def test_http_access(self):
        """Test HTTP access to audio files."""
        logger.info("\n=== TESTING HTTP ACCESS ===")
        
        if not os.path.exists(self.www_audio_path):
            logger.error("❌ Cannot test HTTP - audio directory not found")
            return False
            
        # Get audio files
        audio_files = []
        for file in os.listdir(self.www_audio_path):
            if any(file.lower().endswith(ext) for ext in self.supported_formats):
                file_path = os.path.join(self.www_audio_path, file)
                if os.path.getsize(file_path) > 1024:
                    audio_files.append(file)
        
        if not audio_files:
            logger.error("❌ No audio files to test")
            return False
            
        # Test HTTP access (this would require HA to be running)
        logger.info("ℹ️  HTTP access test requires Home Assistant to be running")
        logger.info("   Test URLs manually:")
        
        for file in audio_files[:3]:  # Test first 3 files
            url = f"http://your-homeassistant-ip:8123/local/solatsyncmy/{file}"
            logger.info(f"   • {url}")
            
        logger.info("\n💡 Replace 'your-homeassistant-ip' with your actual HA IP address")
        logger.info("💡 You should be able to download/play these files in a browser")
        
        return True
    
    def provide_setup_guidance(self):
        """Provide setup guidance based on current state."""
        logger.info("\n=== SETUP GUIDANCE ===")
        
        if not self.ha_config_path:
            logger.info("1. Ensure Home Assistant is installed and running")
            logger.info("2. Check that configuration.yaml exists")
            return
            
        if not os.path.exists(self.www_audio_path):
            logger.info("1. Create the audio directory:")
            logger.info(f"   mkdir -p {self.www_audio_path}")
            logger.info("2. Add your audio files:")
            logger.info(f"   cp your-azan.mp3 {self.www_audio_path}/azan.mp3")
            logger.info(f"   cp your-fajr-azan.mp3 {self.www_audio_path}/azanfajr.mp3")
            return
            
        # Directory exists, check files
        audio_files = []
        if os.path.exists(self.www_audio_path):
            for file in os.listdir(self.www_audio_path):
                if any(file.lower().endswith(ext) for ext in self.supported_formats):
                    file_path = os.path.join(self.www_audio_path, file)
                    if os.path.getsize(file_path) > 1024:
                        audio_files.append(file)
        
        if not audio_files:
            logger.info("1. Add audio files to the directory:")
            logger.info(f"   Directory: {self.www_audio_path}")
            logger.info("2. Recommended files:")
            logger.info("   • azan.mp3 (for normal prayers)")
            logger.info("   • azanfajr.mp3 (for fajr prayer)")
            logger.info("3. Supported formats: MP3, WAV, M4A, OGG, FLAC")
        else:
            logger.info("✅ Setup looks good!")
            logger.info("💡 Test the integration:")
            logger.info("   1. Configure Solat Sync MY integration in Home Assistant")
            logger.info("   2. Use the test_audio service to verify playback")
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("🎵 Local Audio Setup Test for Solat Sync MY")
        logger.info("=" * 50)
        
        # Test 1: Find HA config
        if not self.find_ha_config():
            self.provide_setup_guidance()
            return False
            
        # Test 2: Check directory structure
        dir_ok = self.check_directory_structure()
        
        # Test 3: Check audio files
        files_ok = False
        if dir_ok:
            files_ok = self.check_audio_files()
            
        # Test 4: Test HTTP access
        if files_ok:
            await self.test_http_access()
            
        # Provide guidance
        self.provide_setup_guidance()
        
        logger.info("\n" + "=" * 50)
        if dir_ok and files_ok:
            logger.info("✅ Local audio setup test completed successfully!")
            logger.info("💡 Your audio files should work with the integration")
        else:
            logger.info("⚠️  Local audio setup needs attention")
            logger.info("📖 See AUDIO_SETUP.md for detailed setup instructions")
            
        return dir_ok and files_ok

async def main():
    """Main function."""
    tester = LocalAudioTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 