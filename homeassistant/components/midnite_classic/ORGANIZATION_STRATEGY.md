# Midnite Classic Integration - Entity Organization Strategy

## Overview

This document outlines the organization strategy for the Midnite Classic MPPT integration's entity definitions. The goal is to maintain a clean, maintainable codebase as we add support for the many registers defined in `midnite-registers.json`.

## Current State

The integration currently has entity definitions scattered across multiple files:
- `sensor_definitions.py` - Sensor entity definitions
- `number_definitions.py` - Number entity definitions
- `select_definitions.py` - Select entity definitions
- `button_definitions.py` - Button entity definitions
- `text_definitions.py` - Text entity definitions

As we add more registers from the comprehensive register map, these files will become unwieldy. We need a better organizational structure.

## Proposed File Structure

```
homeassistant/components/midnite_classic/
├── __init__.py
├── manifest.json
├── const.py
├── config_flow.py
├── coordinator.py
├── hub.py
├── sensor.py
├── number.py
├── select.py
├── button.py
├── text.py
├── definitions/
│   ├── __init__.py                    # Exports all definition lists
│   ├── base.py                       # Base definition classes
│   ├── core_status.py                # Core/status registers
│   ├── configuration.py              # Configuration registers
│   ├── diagnostics.py                # Diagnostic registers
│   ├── network.py                    # Network registers
│   ├── specialized.py                # Whizbang, wind, follow-me
│   └── register_groups.py            # Register group definitions
├── helpers/
│   ├── __init__.py
│   ├── temperature_helper.py         # Temperature conversion helper
│   └── write_protection.py           # Write protection logic
└── midnite-registers.json            # Reference document
```

## Register Categorization

### 1. Core/Status Registers (High Priority)
**Purpose**: Essential operational data that users need to monitor frequently
**Polling**: Fast (default coordinator interval)
**Default State**: Enabled by default, not hidden

**Registers**:
- Device info (4101-4104): UNIT_ID, software version, MAC address
- Charge status (4115-4120): Battery voltage, PV voltage, charge stage, internal state
- Power/current (4117-4119, 4121): Battery current, kWh, watts, PV current
- Temperatures (4132-4134): Battery, FET, PCB temperatures
- Daily stats (4118, 4125): Daily kWh, daily amp-hours
- Lifetime stats (4126-4129): Lifetime kWh, lifetime amp-hours

**Entity Types**: Primarily sensors

### 2. Configuration/Settings Registers (Medium Priority)
**Purpose**: User-configurable settings for charging behavior
**Polling**: Medium (can use coordinator default)
**Default State**: Enabled by default, not hidden
**Write Protection**: Requires writes enabled

**Registers**:
- Voltage setpoints (4149-4151, 4155-4156): Absorb, float, equalize, temp compensation voltages
- Time settings (4139, 4143, 4154, 4162-4163): Absorb time, equalize time, intervals
- MPPT mode (4164): MPPT tracking mode selection
- Aux functions (4165-4181): Auxiliary input/output configuration
- Current limits (4148, 4152, 4199): Output current limits
- Battery settings (4244-4249): Nominal voltage, ending amps, rebulk voltage
- Sweep settings (4197-4200): Sweep interval, voltage range, depth

**Entity Types**: Number entities (for writable values), Select entities (for mode selection)

### 3. Diagnostic/Debug Registers (Low Priority)
**Purpose**: Technical information for troubleshooting
**Polling**: Slow (can use coordinator default)
**Default State**: Disabled by default or hidden by default
**Write Protection**: Some require writes enabled

**Registers**:
- Info flags (4104, 4130-4131): System status flags
- Enable flags (4182-4187): Feature enable/disable flags
- Debug registers (4341-4344): Internal debug values
- Communication stats (10001-10062): Modbus communication statistics
- Reset reasons (4142, 4275): Why the device reset or entered resting
- Factory calibration (4188, 4201, 4298-4299, 4300, 4318): Factory settings (read-only)

**Entity Types**: Sensors, some binary sensors for flags

### 4. Network Registers (Rarely Needed)
**Purpose**: Network configuration (usually set via device web interface)
**Polling**: Very slow (on-demand or rarely)
**Default State**: Disabled by default, hidden by default
**Write Protection**: Requires writes enabled

**Registers**:
- IP settings (20481-20493): IP address, gateway, subnet, DNS
- Serial number (20492-20493): Device serial number

**Entity Types**: Text entities, number entities

### 5. Specialized Registers (Optional)
**Purpose**: Advanced features for specific use cases
**Polling**: Medium (depends on feature)
**Default State**: Disabled by default
**Write Protection**: Requires writes enabled

**Registers**:
- Whizbang Jr (4361-4372): Battery monitor integration
- Wind power tables (4300-4316): Wind turbine power curves
- Follow-Me (4328-4334): Multi-unit coordination
- Arc fault (4183): Arc fault protection settings
- LED mode (4207): LED behavior configuration

**Entity Types**: Mixed (sensors, numbers, selects)

## Definition File Pattern

Each definition file should follow this pattern:

```python
"""Core status register definitions."""

from .base import SensorDefinition, NumberDefinition, SelectDefinition

# Core status sensors - always enabled, not hidden
CORE_STATUS_SENSORS = [
    SensorDefinition(
        key="battery_voltage",
        name="Battery Voltage",
        register_address=4115,
        register_group="core",
        unit="V",
        device_class="voltage",
        state_class="measurement
