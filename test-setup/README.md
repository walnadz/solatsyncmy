# Solat Sync MY - Testing Guide

## 🧪 Testing Methods

### Method 1: Docker Container (Recommended)
```bash
cd test-setup
docker-compose up -d
```
Then visit: http://localhost:8123

### Method 2: Manual Installation
1. Copy `custom_components/solatsyncmy/` to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to Settings > Devices & Services > Add Integration
4. Search for "Solat Sync MY"

## 🔍 Testing Checklist

### ✅ Installation Test
- [ ] Integration appears in "Add Integration" list
- [ ] Configuration flow works (select zone)
- [ ] No errors in Home Assistant logs

### ✅ Sensor Test  
- [ ] Prayer time sensors appear (fajr, dhuhr, asr, maghrib, isha)
- [ ] Next prayer sensor shows correct information
- [ ] Hijri date sensor displays correctly
- [ ] All sensors update properly

### ✅ Azan Test
- [ ] Azan switches appear for each prayer
- [ ] Switches can be toggled on/off
- [ ] Azan plays at correct prayer times (when enabled)
- [ ] Service calls work: `solatsyncmy.play_azan`

### ✅ Data Accuracy
- [ ] Prayer times match official Malaysian times
- [ ] Correct timezone handling (Asia/Kuala_Lumpur)
- [ ] Proper zone selection (all Malaysian zones work)

## 🐛 Debugging

Check logs in Home Assistant:
- Settings > System > Logs
- Look for `custom_components.solatsyncmy` entries
- Enable debug logging in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.solatsyncmy: debug
```

## 📋 Test Zones
Try different Malaysian zones:
- `JHR01` - Pulau Aur dan Pemanggil
- `KUL01` - Kuala Lumpur, Putrajaya
- `SGR01` - Johor Bahru, Kota Tinggi
- `PHG01` - Kuantan, Pekan, Rompin
- etc. 