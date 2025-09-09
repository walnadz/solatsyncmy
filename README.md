# Solat Sync MY - Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/walnadz/solatsyncmy.svg?style=flat-square)](https://github.com/walnadz/solatsyncmy/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/walnadz/solatsyncmy.svg?style=flat-square)](https://github.com/walnadz/solatsyncmy/commits/main)
[![License](https://img.shields.io/github/license/walnadz/solatsyncmy.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)

A comprehensive Home Assistant integration for Malaysian prayer times (Waktu Solat) with automated azan playback functionality.

## Features

- **Prayer Time Sensors**: Individual sensors for all five daily prayers (Fajr, Dhuhr, Asr, Maghrib, Isha)
- **Next Prayer Information**: Dedicated sensor showing the next upcoming prayer and time remaining
- **Automated Azan Playback**: Automatically play azan at prayer times through any media player
- **Individual Prayer Control**: Enable/disable azan for specific prayers
- **Malaysian Zones**: Support for all Malaysian prayer time zones
- **Hijri Date**: Display current Hijri date information
- **Real-time Updates**: Automatic daily updates of prayer times
- **Beautiful UI**: Modern configuration interface with dropdown selectors

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/walnadz/solatsyncmy` as a custom repository with category "Integration"
6. Install "Solat Sync MY"
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/walnadz/solatsyncmy/releases)
2. Extract the `solatsyncmy` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for "Solat Sync MY"
4. Select your Malaysian zone from the dropdown
5. Click **Submit**

### Azan Automation Setup

1. Go to the integration's options (click **Configure** on the integration card)
2. Enable "Azan Automation"
3. Select a media player for azan playback
4. Adjust volume level (0.1 - 1.0)
5. Enable/disable azan for individual prayers
6. Click **Submit**

## Entities Created

### Sensors

- `sensor.solatsyncmy_fajr` - Fajr prayer time
- `sensor.solatsyncmy_dhuhr` - Dhuhr prayer time  
- `sensor.solatsyncmy_asr` - Asr prayer time
- `sensor.solatsyncmy_maghrib` - Maghrib prayer time
- `sensor.solatsyncmy_isha` - Isha prayer time
- `sensor.solatsyncmy_next_prayer` - Next prayer information

### Switches

- `switch.solatsyncmy_azan_automation` - Main azan automation toggle
- `switch.solatsyncmy_azan_fajr` - Fajr azan toggle
- `switch.solatsyncmy_azan_dhuhr` - Dhuhr azan toggle
- `switch.solatsyncmy_azan_asr` - Asr azan toggle
- `switch.solatsyncmy_azan_maghrib` - Maghrib azan toggle
- `switch.solatsyncmy_azan_isha` - Isha azan toggle

## Services

### `solatsyncmy.refresh_prayer_times`

Manually refresh prayer times data.

### `solatsyncmy.play_azan`

Manually play azan for a specific prayer.

**Parameters:**
- `prayer` (required): Which prayer's azan to play (fajr, dhuhr, asr, maghrib, isha)
- `media_player` (optional): Media player entity to use
- `volume` (optional): Volume level (0.1-1.0, default: 0.7)

## Malaysian Zones Supported

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

## Automation Examples

### Prayer Time Notifications

```yaml
automation:
  - alias: "Prayer Time Notification"
    trigger:
      - platform: state
        entity_id: sensor.solatsyncmy_next_prayer
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Prayer Time"
          message: "{{ trigger.to_state.state }} prayer time is approaching"
```

### Conditional Azan Playback

```yaml
automation:
  - alias: "Weekend Azan Only"
    trigger:
      - platform: time
        at: sensor.solatsyncmy_fajr
    condition:
      - condition: time
        weekday:
          - sat
          - sun
    action:
      - service: solatsyncmy.play_azan
        data:
          prayer: fajr
          media_player: media_player.bedroom_speaker
          volume: 0.5
```

## Troubleshooting

### Azan Not Playing

1. Ensure azan automation is enabled
2. Check that the selected media player exists and is available
3. Verify azan files are present in the integration directory
4. Check Home Assistant logs for error messages

### Prayer Times Not Updating

1. Check internet connection
2. Verify the API endpoint is accessible
3. Check integration logs for API errors
4. Try refreshing manually using the service

### Zone Not Found

1. Ensure you selected a valid Malaysian zone code
2. Check the zone list in the configuration
3. Reconfigure the integration if needed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Prayer time data provided by [Waktu Solat API](https://api.waktusolat.app/)
- Inspired by the Malaysian Muslim community's need for accurate prayer times
- Built with ❤️ for the Home Assistant community

## Support

If you find this integration helpful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features
- 🔄 Contributing code improvements

---

**Disclaimer**: This integration is not affiliated with JAKIM or any official Malaysian Islamic authorities. Prayer times are provided for convenience and should be verified with local mosque or official sources for religious obligations. 