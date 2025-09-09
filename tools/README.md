# 🛠️ Solat Sync MY Tools

This directory contains diagnostic and testing tools for the Solat Sync MY integration.

## 🎵 Audio Testing Tools

### `test_local_audio.py`

Tests the local audio file setup for the integration.

**What it checks:**
- Home Assistant configuration directory
- `/config/www/solatsyncmy/` directory structure
- Audio file presence and validity
- File formats and sizes
- HTTP accessibility (when HA is running)

**Usage:**
```bash
python tools/test_local_audio.py
```

**Example Output:**
```
🎵 Local Audio Setup Test for Solat Sync MY
==================================================
✅ Found Home Assistant config at: /config
✅ WWW directory exists: /config/www
✅ Audio directory exists: /config/www/solatsyncmy
✅ Found 2 audio file(s):
   • azan.mp3 (3,245 KB)
   • azanfajr.mp3 (2,891 KB)
✅ Standard files found: azan.mp3, azanfajr.mp3
```

**When to use:**
- Setting up local audio files for the first time
- Troubleshooting audio playback issues
- Verifying file locations and accessibility
- Before configuring the integration

## 🚀 Getting Started

1. **Install dependencies** (if running outside Home Assistant):
   ```bash
   pip install aiohttp
   ```

2. **Run the audio test**:
   ```bash
   python tools/test_local_audio.py
   ```

3. **Follow the guidance** provided by the tool to fix any issues

## 📖 Related Documentation

- [Audio Setup Guide](../AUDIO_SETUP.md) - Complete audio file setup instructions
- [Main README](../README.md) - Integration overview and setup
- [Testing Guide](../TESTING_GUIDE.md) - Comprehensive testing procedures

## 🆘 Troubleshooting

If the tools report issues:

1. **Check Home Assistant installation**: Ensure HA is properly installed
2. **Verify file permissions**: Audio files should be readable by HA
3. **Check file formats**: Use MP3, WAV, M4A, OGG, or FLAC
4. **Ensure file sizes**: Files should be > 1KB (not empty placeholders)

## 💡 Contributing

To add new tools:

1. Create the tool script in this directory
2. Make it executable: `chmod +x your_tool.py`
3. Add documentation to this README
4. Include appropriate error handling and logging
5. Follow the existing code style and patterns 