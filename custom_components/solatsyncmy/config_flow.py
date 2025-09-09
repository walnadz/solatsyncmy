"""Config flow for Waktu Solat Malaysia integration."""
import logging
import os
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    DEFAULT_ZONE,
    CONF_ZONE,
    CONF_AZAN_ENABLED,
    CONF_AZAN_SUBUH_ENABLED,
    CONF_AZAN_ZOHOR_ENABLED,
    CONF_AZAN_ASAR_ENABLED,
    CONF_AZAN_MAGHRIB_ENABLED,
    CONF_AZAN_ISYAK_ENABLED,
    CONF_MEDIA_PLAYER,
    CONF_AZAN_VOLUME,
    CONF_AUDIO_SOURCE,
    CONF_REMOTE_AZAN_URL,
    CONF_REMOTE_FAJR_URL,
    AUDIO_SOURCE_BUNDLED,
    AUDIO_SOURCE_OPTIONS,
    AUDIO_SOURCE_DESCRIPTIONS,
)
from .coordinator import WaktuSolatCoordinator

_LOGGER = logging.getLogger(__name__)

# Malaysian zones (simplified list - in production you'd fetch from API)
ZONES = [
    ("JHR01", "Johor - Pulau Aur dan Pulau Pemanggil"),
    ("JHR02", "Johor - Johor Bahru, Kota Tinggi, Mersing, Kulai"),
    ("JHR03", "Johor - Kluang, Pontian"),
    ("JHR04", "Johor - Batu Pahat, Muar, Segamat, Gemas Johor, Tangkak"),
    ("KDH01", "Kedah - Kota Setar, Kubang Pasu, Pokok Sena"),
    ("KDH02", "Kedah - Kuala Muda, Yan, Pendang"),
    ("KDH03", "Kedah - Padang Terap, Sik"),
    ("KDH04", "Kedah - Baling"),
    ("KDH05", "Kedah - Bandar Baharu, Kulim"),
    ("KDH06", "Kedah - Langkawi"),
    ("KDH07", "Kedah - Puncak Gunung Jerai"),
    ("KTN01", "Kelantan - Bachok, Kota Bharu, Machang, Pasir Mas, Pasir Puteh, Tanah Merah, Tumpat, Kuala Krai, Mukim Chiku"),
    ("KTN02", "Kelantan - Gua Musang, Jeli, Jajahan Kecil Lojing"),
    ("MLK01", "Melaka - Seluruh Negeri Melaka"),
    ("NGS01", "Negeri Sembilan - Tampin, Jempol"),
    ("NGS02", "Negeri Sembilan - Jelebu, Kuala Pilah, Rembau"),
    ("NGS03", "Negeri Sembilan - Port Dickson, Seremban"),
    ("PHG01", "Pahang - Pulau Tioman"),
    ("PHG02", "Pahang - Kuantan, Pekan, Muadzam Shah"),
    ("PHG03", "Pahang - Jerantut, Temerloh, Maran, Bera, Chenor, Jengka"),
    ("PHG04", "Pahang - Bentong, Lipis, Raub"),
    ("PHG05", "Pahang - Genting Sempah, Janda Baik, Bukit Tinggi"),
    ("PHG06", "Pahang - Cameron Highlands, Genting Higlands, Bukit Fraser"),
    ("PRK01", "Perak - Tapah, Slim River, Tanjung Malim"),
    ("PRK02", "Perak - Kuala Kangsar, Sg. Siput, Ipoh, Batu Gajah, Kampar"),
    ("PRK03", "Perak - Lenggong, Pengkalan Hulu, Grik"),
    ("PRK04", "Perak - Temengor, Belum"),
    ("PRK05", "Perak - Kg Gajah, Teluk Intan, Bagan Datuk, Seri Iskandar, Beruas, Parit, Lumut, Sitiawan, Pulau Pangkor"),
    ("PRK06", "Perak - Selama, Taiping, Bagan Serai, Parit Buntar"),
    ("PRK07", "Perak - Bukit Larut"),
    ("PLS01", "Perlis - Seluruh Negeri Perlis"),
    ("PNG01", "Pulau Pinang - Seluruh Negeri Pulau Pinang"),
    ("SBH01", "Sabah - Bahagian Sandakan (Timur)"),
    ("SBH02", "Sabah - Beluran, Telupid, Pinangah, Terusan, Kuamut, Bahagian Sandakan (Barat)"),
    ("SBH03", "Sabah - Lahad Datu, Silabukan, Kunak, Sahabat, Semporna, Tungku, Bahagian Tawau (Timur)"),
    ("SBH04", "Sabah - Bandar Tawau, Balong, Merotai, Kalabakan, Bahagian Tawau (Barat)"),
    ("SBH05", "Sabah - Kudat, Kota Marudu, Pitas, Pulau Banggi, Bahagian Kudat"),
    ("SBH06", "Sabah - Gunung Kinabalu"),
    ("SBH07", "Sabah - Kota Kinabalu, Ranau, Kota Belud, Tuaran, Penampang, Papar, Putatan, Bahagian Pantai Barat"),
    ("SBH08", "Sabah - Pensiangan, Keningau, Tambunan, Nabawan, Bahagian Pendalaman (Atas)"),
    ("SBH09", "Sabah - Beaufort, Kuala Penyu, Sipitang, Tenom, Long Pasia, Membakut, Weston, Bahagian Pendalaman (Bawah)"),
    ("SWK01", "Sarawak - Limbang, Lawas, Sundar, Trusan"),
    ("SWK02", "Sarawak - Miri, Niah, Bekenu, Sibuti, Marudi"),
    ("SWK03", "Sarawak - Pandan, Belaga, Suai, Tatau, Sebauh, Bintulu"),
    ("SWK04", "Sarawak - Sibu, Mukah, Dalat, Song, Igan, Oya, Balingian, Kanowit, Kapit"),
    ("SWK05", "Sarawak - Sarikei, Matu, Julau, Rajang, Daro, Bintangor, Belawai"),
    ("SWK06", "Sarawak - Lubok Antu, Sri Aman, Roban, Debak, Kabong, Lingga, Engkelili, Betong, Spaoh, Pusa, Saratok"),
    ("SWK07", "Sarawak - Serian, Simunjan, Samarahan, Sebuyau, Meludam"),
    ("SWK08", "Sarawak - Kuching, Bau, Lundu, Sematan"),
    ("SWK09", "Sarawak - Zon Khas (Kampung Patarikan)"),
    ("SGR01", "Selangor - Gombak, Petaling, Sepang, Hulu Langat, Hulu Selangor, Shah Alam"),
    ("SGR02", "Selangor - Kuala Selangor, Sabak Bernam"),
    ("SGR03", "Selangor - Klang, Kuala Langat"),
    ("TRG01", "Terengganu - Kuala Terengganu, Marang, Kuala Nerus"),
    ("TRG02", "Terengganu - Besut, Setiu"),
    ("TRG03", "Terengganu - Hulu Terengganu"),
    ("TRG04", "Terengganu - Dungun, Kemaman"),
    ("WLY01", "Wilayah Persekutuan - Kuala Lumpur, Putrajaya"),
    ("WLY02", "Wilayah Persekutuan - Labuan"),
]


class WaktuSolatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waktu Solat Malaysia."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the zone
            zone = user_input[CONF_ZONE]
            if any(z[0] == zone for z in ZONES):
                # Validate media player if provided
                media_player = user_input.get(CONF_MEDIA_PLAYER)
                if media_player and not self.hass.states.get(media_player):
                    errors[CONF_MEDIA_PLAYER] = "media_player_not_found"
                else:
                    # Create entry with both zone and media player
                    return self.async_create_entry(
                        title=f"Solat Sync MY ({zone})",
                        data={CONF_ZONE: zone},
                        options={
                            CONF_MEDIA_PLAYER: media_player or "",
                            CONF_AZAN_ENABLED: bool(media_player),  # Enable if media player selected
                            CONF_AZAN_VOLUME: 0.7,
                            CONF_AZAN_SUBUH_ENABLED: True,
                            CONF_AZAN_ZOHOR_ENABLED: True,
                            CONF_AZAN_ASAR_ENABLED: True,
                            CONF_AZAN_MAGHRIB_ENABLED: True,
                            CONF_AZAN_ISYAK_ENABLED: True,
                        }
                    )
            else:
                errors[CONF_ZONE] = "invalid_zone"

        # Get available media players
        media_players = []
        for state in self.hass.states.async_all():
            if state.entity_id.startswith("media_player."):
                media_players.append({
                    "value": state.entity_id,
                    "label": f"{state.attributes.get('friendly_name', state.entity_id)}"
                })

        # Show form
        data_schema = vol.Schema({
            vol.Required(CONF_ZONE, default=DEFAULT_ZONE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": zone[0], "label": zone[1]} for zone in ZONES],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_MEDIA_PLAYER): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=media_players,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ) if media_players else str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "zone_info": "Select your Malaysian prayer time zone",
                "media_player_info": "Optional: Select a media player for automated azan playback"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return WaktuSolatOptionsFlowHandler(config_entry)


class WaktuSolatOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Waktu Solat Malaysia."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # Validate media player if azan is enabled
            if user_input.get(CONF_AZAN_ENABLED, False):
                media_player = user_input.get(CONF_MEDIA_PLAYER)
                if not media_player:
                    errors[CONF_MEDIA_PLAYER] = "media_player_required"
                else:
                    # Validate that the media player exists
                    if not self.hass.states.get(media_player):
                        errors[CONF_MEDIA_PLAYER] = "media_player_not_found"

            # Validate remote URLs if remote audio source is selected
            audio_source = user_input.get(CONF_AUDIO_SOURCE, AUDIO_SOURCE_BUNDLED)
            if audio_source == "remote_urls":
                remote_azan_url = user_input.get(CONF_REMOTE_AZAN_URL, "").strip()
                remote_fajr_url = user_input.get(CONF_REMOTE_FAJR_URL, "").strip()
                
                if not remote_azan_url:
                    errors[CONF_REMOTE_AZAN_URL] = "remote_url_required"
                elif not remote_azan_url.startswith(("http://", "https://")):
                    errors[CONF_REMOTE_AZAN_URL] = "invalid_url_format"
                
                if not remote_fajr_url:
                    errors[CONF_REMOTE_FAJR_URL] = "remote_url_required"
                elif not remote_fajr_url.startswith(("http://", "https://")):
                    errors[CONF_REMOTE_FAJR_URL] = "invalid_url_format"

            if not errors:
                    return self.async_create_entry(title="", data=user_input)

        # Get current options
        current_options = self.config_entry.options
        
        # Get available media players
        media_players = []
        for state in self.hass.states.async_all():
            if state.entity_id.startswith("media_player."):
                media_players.append({
                    "value": state.entity_id,
                    "label": f"{state.attributes.get('friendly_name', state.entity_id)} ({state.entity_id})"
                })

        data_schema = vol.Schema({
            vol.Optional(
                CONF_AZAN_ENABLED,
                default=current_options.get(CONF_AZAN_ENABLED, False),
            ): bool,
            vol.Optional(
                CONF_MEDIA_PLAYER,
                default=current_options.get(CONF_MEDIA_PLAYER, ""),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=media_players,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_AUDIO_SOURCE,
                default=current_options.get(CONF_AUDIO_SOURCE, AUDIO_SOURCE_BUNDLED),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": option, "label": AUDIO_SOURCE_DESCRIPTIONS[option]}
                        for option in AUDIO_SOURCE_OPTIONS
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_REMOTE_AZAN_URL,
                default=current_options.get(CONF_REMOTE_AZAN_URL, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.URL,
                )
            ),
            vol.Optional(
                CONF_REMOTE_FAJR_URL,
                default=current_options.get(CONF_REMOTE_FAJR_URL, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.URL,
                )
            ),
            vol.Optional(
                CONF_AZAN_VOLUME,
                default=current_options.get(CONF_AZAN_VOLUME, 0.7),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.1,
                    max=1.0,
                    step=0.1,
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Optional(
                CONF_AZAN_SUBUH_ENABLED,
                default=current_options.get(CONF_AZAN_SUBUH_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_ZOHOR_ENABLED,
                default=current_options.get(CONF_AZAN_ZOHOR_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_ASAR_ENABLED,
                default=current_options.get(CONF_AZAN_ASAR_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_MAGHRIB_ENABLED,
                default=current_options.get(CONF_AZAN_MAGHRIB_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_ISYAK_ENABLED,
                default=current_options.get(CONF_AZAN_ISYAK_ENABLED, True),
            ): bool,
        })

        # Check for local audio files and build comprehensive info
        www_audio_dir = self.hass.config.path("www", "solatsyncmy")
        audio_info_lines = []
        
        audio_info_lines.append("🎵 Audio Files Status:")
        
        if os.path.exists(www_audio_dir):
            audio_files = []
            for file in os.listdir(www_audio_dir):
                if file.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac')):
                    file_path = os.path.join(www_audio_dir, file)
                    if os.path.getsize(file_path) > 1024:  # > 1KB
                        size_kb = os.path.getsize(file_path) // 1024
                        audio_files.append(f"{file} ({size_kb}KB)")
            
            if audio_files:
                audio_info_lines.append(f"✅ Found {len(audio_files)} file(s):")
                for file_info in audio_files:
                    audio_info_lines.append(f"   • {file_info}")
            else:
                audio_info_lines.append("⚠️  No valid audio files found")
                audio_info_lines.append("   Placeholder files will be created")
        else:
            audio_info_lines.append("ℹ️  Directory will be created: /config/www/solatsyncmy/")
            audio_info_lines.append("   Placeholder files will be created")
        
        audio_info_lines.append("")
        audio_info_lines.append("💡 Local Audio Setup:")
        audio_info_lines.append("• Standard: azan.mp3 (normal), azanfajr.mp3 (fajr)")
        audio_info_lines.append("• Prayer-specific: azan_subuh.mp3, azan_zohor.mp3, etc.")
        audio_info_lines.append("• Formats: MP3, WAV, M4A, OGG, FLAC")
        audio_info_lines.append("• Location: /config/www/solatsyncmy/")
        audio_info_lines.append("• Served as: http://your-ha:8123/local/solatsyncmy/filename.mp3")
        audio_info_lines.append("")
        audio_info_lines.append("📖 See AUDIO_SETUP.md for detailed setup guide")
        
        audio_info = "\n".join(audio_info_lines)

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "audio_info": audio_info,
                "media_player_info": "Select a media player for automated azan playback"
            }
        ) 