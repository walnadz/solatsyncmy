# Solat Sync MY - Media Player Testing Guide

## Overview
This guide helps you test and troubleshoot media player functionality with the Solat Sync MY integration.

## Installation & Setup

1. **Install the Integration**
   - Copy the `custom_components/solatsyncmy` folder to your Home Assistant `config/custom_components/` directory
   - Restart Home Assistant
   - Go to Settings > Devices & Services > Add Integration
   - Search for "Solat Sync MY" and add it

2. **Verify Audio Files**
   - After setup, check that audio files exist in `/config/www/solatsyncmy/`
   - You should see `azan.mp3` and `azanfajr.mp3`

## Testing Services

### 1. Test Audio Service (`solatsyncmy.test_audio`)

This service tests different audio path formats and media types to find what works with your media player.

**Go to Developer Tools > Services:**

```yaml
service: solatsyncmy.test_audio
data:
  media_player: media_player.your_player_name
  audio_file: azan.mp3
  volume: 0.5
```

**What it does:**
- Tests multiple URL formats
- Tests different media content types
- Logs detailed results to help identify what works
- Stops after the first successful attempt

### 2. Play Azan Service (`solatsyncmy.play_azan`)

Once you know your media player works, use this service to play azan:

```yaml
service: solatsyncmy.play_azan
data:
  prayer: fajr
  media_player: media_player.your_player_name
  volume: 0.5
```

## Common Media Player Entity Names

- `media_player.bedroom_speaker`
- `media_player.living_room_speaker`
- `media_player.kitchen_display`
- `media_player.your_homepod`
- `media_player.your_android_tv`

To find your media player names:
1. Go to Settings > Devices & Services
2. Look for your media players
3. Click on them to see their entity IDs

## Troubleshooting

### Check Logs
After running tests, check Home Assistant logs for detailed information:
- Settings > System > Logs
- Look for entries from `custom_components.solatsyncmy`

### Common Issues

1. **"Media player not found"**
   - Check the entity ID is correct
   - Ensure the media player is turned on and available

2. **"Audio file not found"**
   - Restart Home Assistant to trigger file setup
   - Check `/config/www/solatsyncmy/` folder exists and contains audio files

3. **"All attempts failed"**
   - Your media player might not support the audio formats
   - Try different media players
   - Check if the media player supports HTTP URLs

### Media Player Specific Tips

**HomePod/Apple Devices:**
- The integration tries both with and without the `announce` parameter
- Uses `music` content type first for better compatibility

**Android TV:**
- Prioritizes `audio/mpeg` and `video/mp4` formats
- Some Android TVs are picky about audio formats

**Google Speakers:**
- Usually work well with standard `/local/` paths
- Try `audio/mp3` content type

## Path Formats Tested

The integration automatically tests these path formats:

1. `/local/solatsyncmy/azan.mp3` (Standard HA path)
2. `media-source://media_source/local/solatsyncmy/azan.mp3` (Media source)
3. `http://your-ha-url/local/solatsyncmy/azan.mp3` (Full URL)
4. `http://localhost:8123/local/solatsyncmy/azan.mp3` (Localhost)
5. `/media/local/solatsyncmy/azan.mp3` (Alternative path)
6. `media-source://media_source/local/azan.mp3` (Direct media source)
7. `/local/azan.mp3` (Root www path)

## Content Types Tested

- `audio/mp3`
- `audio/mpeg`  
- `music`
- `audio`
- `audio/aac` (Apple devices)
- `video/mp4` (Android TV)

## Getting Help

If you're still having issues:

1. Run the `test_audio` service and check the logs
2. Note which media player you're using
3. Note any error messages from the logs
4. Check if manual media playback works in Home Assistant

The detailed logging from the test service will help identify the exact issue with your setup. 