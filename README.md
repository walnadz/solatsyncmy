# Solat Sync MY - Malaysian Prayer Times Integration

A comprehensive Home Assistant integration for Malaysian prayer times with automated azan (call to prayer) playback using local Malaysian time zones.

## ✨ Features

- **🕌 Accurate Prayer Times**: Real-time prayer times for all Malaysian zones
- **🔊 Automated Azan Playback**: Customizable azan automation for each prayer
- **🎵 Local Audio Support**: Support for custom azan files and local playback
- **📱 Smart Media Player Control**: Automatic power-on and volume management
- **🇲🇾 Malay Prayer Names**: Uses authentic Malay prayer names (Subuh, Zohor, Asar, Maghrib, Isyak)
- **⏰ Next Day Prayer Times**: Shows next day times after Isyak
- **🛠️ Advanced Diagnostics**: Built-in audio testing and troubleshooting tools

## 📦 Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the **+** button
4. Search for "Solat Sync MY"
5. Click **Install**
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/walnadz/solatsyncmy/releases)
2. Extract the files to `custom_components/solatsyncmy/` in your Home Assistant config directory
3. Restart Home Assistant

## ⚙️ Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Solat Sync MY"
4. Select your Malaysian zone from the dropdown
5. **Optional**: Select a media player for automated azan playback
6. Click **Submit**

### Azan Automation Setup

1. Go to the integration's options (click **Configure** on the integration card)
2. Enable "Azan Automation"
3. Select a media player for azan playback
4. Adjust volume level (0.1 - 1.0)
5. Enable/disable azan for individual prayers:
   - **Azan Subuh** (Fajr)
   - **Azan Zohor** (Dhuhr)
   - **Azan Asar** (Asr)
   - **Azan Maghrib** (Maghrib)
   - **Azan Isyak** (Isha)
6. Click **Submit**

## 🎵 Local Audio Files

### Adding Your Own Azan Files

1. **Place audio files** in Home Assistant's `config/www/solatsyncmy/` directory
2. **Supported formats**: MP3, WAV, M4A, OGG
3. **File names**:
   - `azan.mp3` - For Zohor, Asar, Maghrib, Isyak
   - `azanfajr.mp3` - For Subuh (different azan)

### Custom Prayer-Specific Files

You can also use prayer-specific files:
- `azan_fajr.mp3` or `subuh.mp3` - For Subuh
- `azan_dhuhr.mp3` or `zohor.mp3` - For Zohor  
- `azan_asr.mp3` or `asar.mp3` - For Asar
- `azan_maghrib.mp3` or `maghrib.mp3` - For Maghrib
- `azan_isha.mp3` or `isyak.mp3` - For Isyak

### Audio File Locations

The integration automatically scans these locations:
- `/config/www/solatsyncmy/` (recommended)
- `/config/www/`
- `/config/media/`
- `/media/`
- `/share/`

## 📊 Entities Created

### Sensors

- `sensor.solatsyncmy_subuh` - Subuh (Fajr) prayer time
- `sensor.solatsyncmy_zohor` - Zohor (Dhuhr) prayer time  
- `sensor.solatsyncmy_asar` - Asar (Asr) prayer time
- `sensor.solatsyncmy_maghrib` - Maghrib prayer time
- `sensor.solatsyncmy_isyak` - Isyak (Isha) prayer time
- `sensor.solatsyncmy_next_prayer` - Next prayer information

### Switches (Ordered for Better Control)

1. `switch.solatsyncmy_azan_automation` - **Main azan automation toggle**
2. `switch.solatsyncmy_azan_subuh` - Subuh azan toggle
3. `switch.solatsyncmy_azan_zohor` - Zohor azan toggle
4. `switch.solatsyncmy_azan_asar` - Asar azan toggle
5. `switch.solatsyncmy_azan_maghrib` - Maghrib azan toggle
6. `switch.solatsyncmy_azan_isyak` - Isyak azan toggle

## 🛠️ Services

### `solatsyncmy.play_azan`

Manually play azan for a specific prayer.

**Parameters:**
- `prayer` (required): Prayer name (fajr, dhuhr, asr, maghrib, isha)
- `media_player` (required): Media player entity ID
- `volume` (optional): Volume level (0.1-1.0, default: 0.7)

### `solatsyncmy.test_audio`

Test audio playback with comprehensive diagnostics.

**Parameters:**
- `media_player` (required): Media player entity ID
- `audio_file` (optional): Audio file to test (default: azan.mp3)
- `volume` (optional): Volume level (0.1-1.0, default: 0.5)

## 🇲🇾 Malaysian Zones Supported

The integration supports all official Malaysian prayer time zones:

- **Johor**: JHR01, JHR02, JHR03, JHR04
- **Kedah**: KDH01-KDH07
- **Kelantan**: KTN01, KTN02
- **Melaka**: MLK01
- **Negeri Sembilan**: NGS01, NGS02, NGS03
- **Pahang**: PHG01-PHG06
- **Perak**: PRK01-PRK07
- **Perlis**: PLS01
- **Pulau Pinang**: PNG01
- **Sabah**: SBH01-SBH09
- **Sarawak**: SWK01-SWK09
- **Selangor**: SGR01, SGR02, SGR03
- **Terengganu**: TRG01-TRG04
- **Wilayah Persekutuan**: WLY01 (KL/Putrajaya), WLY02 (Labuan)

## 🚀 Advanced Features

### Smart Prayer Time Display

- **Current Day**: Shows today's prayer times
- **After Isyak**: Automatically shows next day's prayer times
- **Next Prayer Calculation**: Intelligent next prayer detection

### Enhanced Audio System

- **Auto Power-On**: Automatically turns on media players
- **Smart Timing**: Proper delays between commands
- **Success Verification**: Confirms playback started
- **Local File Priority**: Prefers local custom files
- **Fallback Support**: Multiple audio source locations

### Troubleshooting Tools

- **Built-in Diagnostics**: Comprehensive audio testing
- **File Detection**: Automatic audio file scanning
- **Debug Logging**: Detailed step-by-step logging
- **Error Recovery**: Graceful handling of failed playback

## 🐛 Troubleshooting

### Audio Not Playing?

1. **Test your setup**: Use the `solatsyncmy.test_audio` service
2. **Check files**: Ensure audio files exist in `/config/www/solatsyncmy/`
3. **Media player**: Verify your media player is working
4. **File size**: Ensure audio files are > 1KB (not placeholders)
5. **Check logs**: Look for integration logs in Settings → System → Logs

### Common Issues

- **Media player not found**: Ensure entity ID is correct
- **Audio files missing**: Place MP3 files in correct directory
- **Network issues**: Check Home Assistant's network connectivity
- **Volume too low**: Increase volume in configuration

## 📝 Changelog

### v1.0.12 - Major Enhancements
- ✅ **Malay Prayer Names**: Subuh, Zohor, Asar, Maghrib, Isyak
- ✅ **Media Player Setup**: Added to initial configuration
- ✅ **Control Ordering**: Main automation first, then prayers in order
- ✅ **Next Day Times**: Shows next day prayer times after Isyak
- ✅ **Local Audio Support**: Enhanced local file detection and playback
- ✅ **Advanced Diagnostics**: Comprehensive audio testing tools
- ✅ **Smart Audio System**: Auto power-on, timing, and verification

### v1.0.11 - Audio Playback Fix
- 🔧 Fixed media player state management
- 🔧 Added proper command timing
- 🔧 Enhanced error handling and logging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- Malaysian prayer time data from [Waktu Solat API](https://api.waktusolat.app)
- Islamic community feedback and testing
- Home Assistant community support

---

**🕌 May this integration help you maintain your daily prayers. Barakallahu feeki.** 