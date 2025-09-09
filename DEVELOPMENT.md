# 🛠️ Development Guide - SolatSync MY

This guide helps you develop and test changes directly on your Home Assistant server.

## 📋 Setup Complete ✅

Your development environment is now configured:
- **Local Development**: `/Users/nadz/Downloads/solatsyncmy`
- **HA Server**: `nadzr@192.168.0.114:/ha/config/custom_components/solatsyncmy`
- **Latest Code**: ✅ Synced to HA server

## 🚀 Development Workflow

### 1. **Full Deployment** (Recommended for major changes)
```bash
./sync_to_ha.sh "Your commit message"
```
**What it does:**
- Commits and pushes changes to GitHub
- Syncs all files to HA server
- Restarts Home Assistant
- Shows status after restart

### 2. **Quick Sync** (For minor changes/debugging)
```bash
./quick_sync.sh
```
**What it does:**
- Syncs only Python/config files (no audio)
- No HA restart (faster iteration)
- You may need to reload integration manually

### 3. **Manual Sync** (If scripts fail)
```bash
scp -r custom_components/solatsyncmy/* nadzr@192.168.0.114:/ha/config/custom_components/solatsyncmy/
```

## 🎯 Development Tips

### **Testing Audio Changes**
1. Make changes to audio-related code
2. Use full deployment: `./sync_to_ha.sh "Fix audio issue"`
3. Test using Developer Tools → Services:
   ```yaml
   service: solatsyncmy.test_audio
   target:
     entity_id: switch.your_prayer_times
   ```

### **Testing UI/Config Changes**
1. Make changes to `config_flow.py`, `strings.json`
2. Use quick sync: `./quick_sync.sh`
3. Go to Settings → Integrations → SolatSync MY → Configure

### **Testing Sensor Updates**
1. Make changes to `sensor.py`, `coordinator.py`
2. Use quick sync: `./quick_sync.sh`
3. Check entities in Developer Tools → States

### **Debugging**
1. Check HA logs: SSH to server and run:
   ```bash
   sudo tail -f /ha/config/home-assistant.log | grep -i solat
   ```
2. Or check via HA UI: Settings → System → Logs

## 📂 Key Files

| File | Purpose | When to Edit |
|------|---------|--------------|
| `__init__.py` | Main component logic | Core functionality changes |
| `sensor.py` | Prayer time sensors | Prayer time calculations |
| `switch.py` | Prayer switches & audio | Audio playback, notifications |
| `config_flow.py` | Setup UI | Configuration options |
| `coordinator.py` | Data fetching | API integration |
| `services.yaml` | Service definitions | Adding new services |

## 🔄 HA Integration Management

### **Reload Integration**
Settings → Integrations → SolatSync MY → ⋮ → Reload

### **Restart HA Core**
Settings → System → Restart → Quick Restart

### **Full HA Restart**
```bash
ssh nadzr@192.168.0.114 "sudo systemctl restart home-assistant@homeassistant"
```

## 🐛 Troubleshooting

### **SSH Issues**
- Make sure you can SSH without scripts: `ssh nadzr@192.168.0.114`
- Check your SSH key or password authentication

### **Permission Issues**
```bash
ssh nadzr@192.168.0.114 "sudo chown -R nadzr:nadzr /ha/config/custom_components/solatsyncmy"
```

### **Integration Not Loading**
1. Check syntax errors: `python -m py_compile custom_components/solatsyncmy/*.py`
2. Check HA logs for errors
3. Verify `manifest.json` is valid JSON

### **Audio Not Playing**
1. Test media player: HA → Developer Tools → Services → `media_player.play_media`
2. Check audio file paths and permissions
3. Use the debug service: `solatsyncmy.test_audio`

## 📊 Quick Commands

```bash
# Full deployment with commit
./sync_to_ha.sh "Add new feature"

# Quick iteration
./quick_sync.sh

# Check HA status
ssh nadzr@192.168.0.114 "sudo systemctl status home-assistant@homeassistant"

# View live logs
ssh nadzr@192.168.0.114 "sudo journalctl -u home-assistant@homeassistant -f"

# Test Python syntax
python -m py_compile custom_components/solatsyncmy/*.py
```

Happy coding! 🎉 