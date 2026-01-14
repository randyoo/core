"""Test the Midnite Classic config flow."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from homeassistant import config_entries
from homeassistant.components.midnite_classic.const import DEFAULT_PORT, DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

_LOGGER = logging.getLogger(__name__)

TEST_HOST = "192.168.1.100"
TEST_MAC = "AA:BB:CC:DD:EE:FF"


@pytest.fixture
def mock_dhcp_service_info() -> MagicMock:
    """Return a mocked DHCP service info."""
    dhcp_info = MagicMock()
    dhcp_info.ip = TEST_HOST
    dhcp_info.macaddress = TEST_MAC
    return dhcp_info


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test successful user flow with manual entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test form submission
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: TEST_HOST, CONF_PORT: DEFAULT_PORT}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Midnite Classic @ {TEST_HOST}"
    assert result["data"][CONF_HOST] == TEST_HOST
    assert result["data"][CONF_PORT] == DEFAULT_PORT


async def test_user_flow_missing_host(hass: HomeAssistant) -> None:
    """Test user flow with missing host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test form submission without host
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PORT: DEFAULT_PORT}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "missing_host"}


async def test_user_flow_duplicate_entry(hass: HomeAssistant) -> None:
    """Test prevention of duplicate entries."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: TEST_HOST, CONF_PORT: DEFAULT_PORT}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Try to create duplicate entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: TEST_HOST, CONF_PORT: DEFAULT_PORT}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_dhcp_flow_success(
    hass: HomeAssistant, mock_dhcp_service_info: MagicMock
) -> None:
    """Test successful DHCP discovery flow."""
    # Simulate DHCP discovery
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=mock_dhcp_service_info,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Confirm discovery
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Midnite Classic @ {TEST_HOST}"
    assert result["data"][CONF_HOST] == TEST_HOST
    assert result["data"][CONF_PORT] == DEFAULT_PORT


async def test_dhcp_flow_duplicate(
    hass: HomeAssistant, mock_dhcp_service_info: MagicMock
) -> None:
    """Test DHCP discovery with already configured device."""
    # Create existing entry
    existing_entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title=f"Midnite Classic @ {TEST_HOST}",
        source=config_entries.SOURCE_USER,
        data={CONF_HOST: TEST_HOST, CONF_PORT: DEFAULT_PORT},
        unique_id=mock_dhcp_service_info.macaddress,
    )
    existing_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(existing_entry)

    # Try DHCP discovery for same device
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=mock_dhcp_service_info,
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_dhcp_flow_ip_update(
    hass: HomeAssistant, mock_dhcp_service_info: MagicMock
) -> None:
    """Test DHCP discovery updates IP for existing device."""
    # Create existing entry with different IP
    old_host = "192.168.1.50"
    existing_entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title=f"Midnite Classic @ {old_host}",
        source=config_entries.SOURCE_USER,
        data={CONF_HOST: old_host, CONF_PORT: DEFAULT_PORT},
        unique_id=mock_dhcp_service_info.macaddress,
    )
    existing_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(existing_entry)

    # DHCP discovery should update IP
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=mock_dhcp_service_info,
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == TEST_HOST  # Updated IP
    assert result["data"][CONF_PORT] == DEFAULT_PORT


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Midnite Classic",
        source=config_entries.SOURCE_USER,
        data={CONF_HOST: TEST_HOST, CONF_PORT: DEFAULT_PORT},
        unique_id=None,
    )
    entry.add_to_hass(hass)

    # Verify options flow is not implemented (returns None)
    assert await hass.config_entries.options.async_init(entry.entry_id) is None
