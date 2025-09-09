# 🎵 Audio Setup Guide for Solat Sync MY

This guide explains how to configure and set up audio sources for automated azan playback in Home Assistant.

## 🎛️ Audio Source Configuration

The integration now supports **4 different audio source options** to give you full control over how azan audio is provided:

### 1. **Bundled Audio Files (with User Override)** 🔄 *[Default]*
- **What it does**: Uses included azan files, but allows you to override with your own
- **Best for**: Most users who want it to work out-of-the-box
- **How it works**:
  1. Integration includes high-quality azan files (~14MB)
  2. Files are automatically copied to `/config/www/solatsyncmy/`
  3. You can replace these files with your own versions
  4. Your files take precedence over bundled ones

### 2. **User-Uploaded Files Only** 📁
- **What it does**: Only uses files you manually upload
- **Best for**: Users who want complete control and smaller integration size
- **How it works**:
  1. No bundled files are used
  2. You must upload your own audio files
  3. Integration will only work after you add files

### 3. **Remote URLs from Internet** 🌐
- **What it does**: Streams azan audio directly from internet URLs
- **Best for**: Users with stable internet who want centrally managed audio
- **How it works**:
  1. You provide HTTP/HTTPS URLs for azan files
  2. Audio is streamed directly from the internet
  3. No local storage required

### 4. **Mixed: Local Preferred, Bundled Fallback** 🔀
- **What it does**: Uses your local files first, falls back to bundled files
- **Best for**: Users who want reliability with customization
- **How it works**:
  1. Checks for your custom files first
  2. Falls back to bundled files if none found
  3. Best of both worlds approach

## ⚙️ Configuration Steps

### Step 1: Choose Your Audio Source

1. Go to **Settings** → **Integrations** → **Solat Sync MY** → **Configure**
2. Under **Audio Source**, select your preferred option:
   - `Bundled audio files (with user override)` - Default, works immediately
   - `User-uploaded files only` - Requires manual file upload
   - `Remote URLs from internet` - Requires internet URLs
   - `Mixed: Local preferred, bundled fallback` - Hybrid approach

### Step 2A: For Remote URLs 🌐

If you selected "Remote URLs from internet":

1. **Remote Azan URL**: Enter the full HTTP/HTTPS URL for normal prayers
   - Example: `https://example.com/audio/azan-normal.mp3`
   - Used for: Zohor, Asar, Maghrib, Isyak

2. **Remote Fajr URL**: Enter the full HTTP/HTTPS URL for Fajr prayer
   - Example: `https://example.com/audio/azan-fajr.mp3`
   - Used for: Subuh/Fajr prayer

**Requirements:**
- URLs must be publicly accessible
- Must start with `http://` or `https://`
- Audio files should be in supported formats (MP3, WAV, M4A, OGG, FLAC)

### Step 2B: For Local Files 📁

If you selected "User-uploaded files only" or want to override bundled files:

1. **Create directory**: `/config/www/solatsyncmy/`
2. **Upload your files** using one of these methods:

#### Method 1: File Manager Add-on (Recommended)
1. Install "File editor" or "Advanced SSH & Web Terminal" add-on
2. Navigate to `/config/www/solatsyncmy/`
3. Upload your audio files

#### Method 2: Samba Share
1. Enable Samba add-on
2. Navigate to `config/www/solatsyncmy/`
3. Copy your files

#### Method 3: SSH/Terminal
```bash
mkdir -p /config/www/solatsyncmy/
cp /path/to/your/azan.mp3 /config/www/solatsyncmy/
cp /path/to/your/azanfajr.mp3 /config/www/solatsyncmy/
```

## 📋 File Naming Options

### Standard Files (Recommended)
```
azan.mp3      # Used for all normal prayers (Zohor, Asar, Maghrib, Isyak)
azanfajr.mp3  # Used specifically for Fajr/Subuh prayer
```

### Prayer-Specific Files
You can also use prayer-specific files that will override the standard files:
```
azan_subuh.mp3    # Fajr/Subuh
azan_zohor.mp3    # Zohor  
azan_asar.mp3     # Asar
azan_maghrib.mp3  # Maghrib
azan_isyak.mp3    # Isyak
```

### Alternative Names
The integration also recognizes these alternative naming patterns:
```
adhan_fajr.mp3, adhan_zohor.mp3, etc.
subuh.mp3, zohor.mp3, asar.mp3, maghrib.mp3, isyak.mp3
```

## 🎧 Supported Audio Formats

- **MP3** (Recommended)
- **WAV** 
- **M4A**
- **OGG**
- **FLAC**

## 🌐 How It Works

### Local Files
1. **Local Access**: Files are served via Home Assistant's built-in web server
2. **URL Format**: `http://your-ha-ip:8123/local/solatsyncmy/filename.mp3`
3. **Automatic Detection**: The integration automatically scans for available files
4. **Priority**: Prayer-specific files take precedence over standard files

### Remote URLs
1. **Direct Streaming**: Audio is streamed directly from the provided URLs
2. **No Local Storage**: No files stored on your Home Assistant instance
3. **Internet Required**: Requires stable internet connection for playback

## ✅ Verification

After configuring your audio source, verify it's working:

### 1. Via Integration Settings
- Go to Settings → Integrations → Solat Sync MY → Configure
- Check the "Audio Files Status" section
- You'll see detected files or configured URLs

### 2. Via Web Browser (Local Files Only)
- Visit: `http://your-ha-ip:8123/local/solatsyncmy/azan.mp3`
- You should be able to download/play the file

### 3. Via Test Service
Use the `solatsyncmy.test_audio` service:

```yaml
service: solatsyncmy.test_audio
data:
  media_player: media_player.your_speaker
  audio_file: azan.mp3
  volume: 0.5
```

## 🚨 Troubleshooting

### Audio Source Issues

#### Bundled Files Not Working
- **Check logs**: Look for "Copied bundled audio file" messages
- **Restart HA**: Restart Home Assistant to trigger file setup
- **Check permissions**: Ensure HA can write to `/config/www/`

#### Local Files Not Found
- **Check file location**: Ensure files are in `/config/www/solatsyncmy/`
- **Check file size**: Files must be > 1KB (not empty placeholders)
- **Check permissions**: Ensure Home Assistant can read the files
- **Check format**: Use supported audio formats (MP3 recommended)

#### Remote URLs Not Working
- **Check URL format**: Must start with `http://` or `https://`
- **Test URLs**: Try opening URLs in a web browser
- **Check internet**: Ensure Home Assistant has internet access
- **Check media player**: Some players don't support streaming URLs

### Playback Issues
- **Test media player**: Ensure your media player works with other audio
- **Check volume**: Try different volume levels (0.1-1.0)
- **Check network**: For network speakers, ensure stable connection
- **Check logs**: Look at Home Assistant logs for detailed error messages

### Configuration Issues
- **Required fields**: Remote URLs are required when using remote source
- **URL validation**: URLs must be properly formatted
- **Media player**: Media player must be selected when azan is enabled

## 📊 File Size Recommendations

### Local Files
- **Typical azan duration**: 2-4 minutes
- **MP3 quality**: 128-192 kbps is sufficient
- **Expected file size**: 2-6 MB per file
- **Storage consideration**: Total ~10-30 MB for all prayer files

### Remote Files
- **No local storage**: Files are streamed, no local space used
- **Bandwidth**: Consider data usage for repeated playback
- **Reliability**: Depends on internet connection stability

## 🔄 Switching Audio Sources

You can change audio sources at any time:

1. Go to Settings → Integrations → Solat Sync MY → Configure
2. Change the "Audio Source" option
3. Configure any required settings (URLs for remote, files for local)
4. Save configuration
5. Test with the `test_audio` service

**Note**: Switching sources takes effect immediately, no restart required.

## 💡 Best Practices

### For Most Users
- **Start with bundled**: Use the default "Bundled with override" option
- **Customize later**: Replace bundled files with your preferred azan if desired

### For Advanced Users
- **Mixed source**: Use "Mixed fallback" for reliability with customization
- **Local only**: Use "User-uploaded only" for complete control
- **Remote URLs**: Use for centralized management across multiple HA instances

### For Network Efficiency
- **Local files**: Better for limited internet or network speakers
- **Remote URLs**: Better for saving local storage space

## 🔧 Advanced Configuration

### Custom File Locations
The integration checks files in this priority order:
1. Prayer-specific files (`azan_subuh.mp3`, etc.)
2. Standard files (`azan.mp3`, `azanfajr.mp3`)
3. Alternative naming patterns

### URL Requirements for Remote Sources
- Must be publicly accessible (no authentication)
- Should support HTTP range requests for better compatibility
- HTTPS recommended for security
- Content-Type should be properly set by the server

### Integration with Media Players
Different media players have different capabilities:
- **Local files**: Supported by all media players
- **Remote URLs**: May not be supported by all players
- **Streaming**: Some players handle streaming better than others

Test your specific media player with your chosen audio source to ensure compatibility. 