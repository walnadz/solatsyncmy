"""Config flow for Waktu Solat Malaysia integration."""
import logging
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
    CONF_AZAN_FAJR_ENABLED,
    CONF_AZAN_DHUHR_ENABLED,
    CONF_AZAN_ASR_ENABLED,
    CONF_AZAN_MAGHRIB_ENABLED,
    CONF_AZAN_ISHA_ENABLED,
    CONF_MEDIA_PLAYER,
    CONF_AZAN_VOLUME,
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
                # Create entry
                return self.async_create_entry(
                    title=f"Solat Sync MY ({zone})",
                    data=user_input,
                )
            else:
                errors[CONF_ZONE] = "invalid_zone"

        # Show form
        data_schema = vol.Schema({
            vol.Required(CONF_ZONE, default=DEFAULT_ZONE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": zone[0], "label": zone[1]} for zone in ZONES],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
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
        self.config_entry = config_entry

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

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        # Get current options
        current_options = self.config_entry.options
        
        # Get available media players
        media_players = []
        for entity_id, state in self.hass.states.async_all():
            if entity_id.startswith("media_player."):
                media_players.append({
                    "value": entity_id,
                    "label": f"{state.attributes.get('friendly_name', entity_id)} ({entity_id})"
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
                CONF_AZAN_FAJR_ENABLED,
                default=current_options.get(CONF_AZAN_FAJR_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_DHUHR_ENABLED,
                default=current_options.get(CONF_AZAN_DHUHR_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_ASR_ENABLED,
                default=current_options.get(CONF_AZAN_ASR_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_MAGHRIB_ENABLED,
                default=current_options.get(CONF_AZAN_MAGHRIB_ENABLED, True),
            ): bool,
            vol.Optional(
                CONF_AZAN_ISHA_ENABLED,
                default=current_options.get(CONF_AZAN_ISHA_ENABLED, True),
            ): bool,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        ) 