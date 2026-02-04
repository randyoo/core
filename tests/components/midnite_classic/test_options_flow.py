"""Test the Midnite Classic options flow."""

from __future__ import annotations

from typing import cast

import pytest

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

pytestmark = pytest.mark.usefixtures("hass")

DOMAIN = "midnite_classic"
CONF_SCAN_INTERVAL = "scan_interval"


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Midnite Classic @ 192.168.1.100",
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
        },
        options={
            "enable_writes": False,
            CONF_SCAN_INTERVAL: 15,
        },
    )


async def test_options_flow_init(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test the options flow initialization."""
    # Add the config entry to hass
    mock_config_entry.add_to_hass(hass)

    # Setup the integration first
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result_dict = cast(dict[str, str | FlowResultType], result)
    assert result_dict["type"] == FlowResultType.FORM
    assert result_dict["step_id"] == "init"


async def test_options_flow_submit(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test the options flow submission."""
    # Add the config entry to hass
    mock_config_entry.add_to_hass(hass)

    # Setup the integration first
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Initialize the options flow
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result_dict = cast(dict[str, str | FlowResultType], result)

    # Submit new options
    user_input = {
        "enable_writes": True,
        CONF_SCAN_INTERVAL: 30,
    }

    result = await hass.config_entries.options.async_configure(
        flow_id=result_dict["flow_id"],
        user_input=user_input,
    )

    result_dict = cast(dict[str, str | FlowResultType], result)
    assert result_dict["type"] == FlowResultType.CREATE_ENTRY
    assert result_dict["data"]["enable_writes"] is True
    assert result_dict["data"][CONF_SCAN_INTERVAL] == 30

    # Verify the options were updated
    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert entry is not None
    assert entry.options["enable_writes"] is True
    assert entry.options[CONF_SCAN_INTERVAL] == 30
