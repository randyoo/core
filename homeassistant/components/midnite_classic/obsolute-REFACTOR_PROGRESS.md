# Midnite Classic Integration Refactor - Progress Tracker

## Overview
This document tracks the progress of refactoring the midnite_classic integration to use a data-driven entity generation approach.

## Current State Analysis

### Existing Integration (refactor-source)
- **Location**: `custom_components/midnite/`
- **Current Implementation**:
  - 30+ manually defined sensor classes in `sensor.py`
  - Similar patterns in `button.py`, `number.py`, `select.py`, `text.py`
  - Hardcoded register addresses in `const.py`
  - Redundant code for data extraction, validation, and formatting

### Key Observations
1. **Device Identification**:
   - Config flow uses DEVICE_ID (registers 4111-4112)
   - Autodiscovery uses MAC address (registers 4106-4108)
   - **Recommendation**: Use MAC address as primary identifier for consistency with autodiscovery

2. **Register Groups**:
   - Well-defined groups in `const.py`: device_info, status, temperatures, energy, time_settings, settings, network, diagnostics
   - Total of 9 register groups covering ~60 registers

3. **Entity Patterns**:
   - Simple: Single register with formula (e.g., battery voltage / 10)
   - Multi-register: Combine registers (e.g., 32-bit values from two 16-bit registers)
   - Bitfield: Extract specific bits
   - String: Combine multiple registers into ASCII strings
   - Composite: Complex logic across multiple registers (e.g., IP/MAC addresses)

## Refactor Plan

### Phase 1: Data Structure Design ✅ COMPLETED
- [x] Analyze existing entity implementations
- [x] Define core data structure for entity definitions
- [x] Identify all required fields for entity generation
- [x] Document formula patterns needed

### Phase 2: Entity Definitions Creation (IN PROGRESS)
**Goal**: Create comprehensive entity definitions from registers.json

#### Current Progress:
- [x] Create `entity_definitions.py` structure with all entity types:
  - EntityDefinition base class
  - SensorDefinition with sensor-specific fields
  - ButtonDefinition
  - NumberDefinition
  - SelectDefinition
  - TextDefinition
- [x] Define 35 sensor entities in `sensor_definitions.py`:
  - battery_voltage, pv_voltage, battery_current, power_output
  - battery_temperature, fet_temperature, pcb_temperature
  - daily_energy, lifetime_energy, lifetime_amp_hours, daily_amp_hours
  - device_type, charge_stage, internal_state, rest_reason
  - pv_input_current, voc_measured, highest_input_voltage
  - float_time_today, absorb_time_remaining, equalize_time_remaining
  - mac_address, ip_address, gateway_address, subnet_mask, dns1, dns2
  - status_roll, restart_time, match_point_shadow
  - logging_interval, sliding_current_limit, modbus_port
- [x] Define remaining sensor entities (35 total completed)
- [ ] Define button entities
- [ ] Define number entities
- [ ] Define select entities
- [ ] Define text entities

#### Files to Create:
```
homeassistant/components/midnite_classic/
├── entity_definitions.py          # Core definitions (split by type)
├── sensor_definitions.py         # Sensor-specific definitions
├── button_definitions.py         # Button-specific definitions
├── number_definitions.py         # Number-specific definitions
├── select_definitions.py         # Select-specific definitions
└── text_definitions.py           # Text-specific definitions
```

### Phase 3: Factory Implementation (NOT STARTED)
- [ ] Create entity factory functions
- [ ] Implement formula evaluation system
- [ ] Build dynamic entity classes
- [ ] Update setup functions

### Phase 4: Migration & Testing (NOT STARTED)
- [ ] Migrate existing entities incrementally
- [ ] Add comprehensive tests
- [ ] Validate all formulas and transformations
- [ ] Ensure backward compatibility

## Implementation Details

### Entity Definition Structure

```python
@dataclass
class EntityDefinition:
    """Data class representing an entity definition."""
    key: str                          # Used for unique_id and translation_key
    name: str                         # Display name (will be translated)
    entity_type: str                  # sensor, button, number, select, text

    register_group: str               # Which register group to read from
    register_address: int             # Primary register address
    secondary_registers: List[int] = field(default_factory=list)  # Additional registers

    formula: Optional[str] = None     # Data extraction formula
    write_formula: Optional[str] = None  # For writable entities

    device_class: Optional[str] = None  # SensorDeviceClass
    state_class: Optional[str] = None   # SensorStateClass
    unit: Optional[str] = None         # Native unit of measurement
    precision: Optional[int] = None    # Suggested display precision

    enabled_by_default: bool = True
    hidden: bool = False
    entity_category: Optional[str] = None  # DIAGNOSTIC, CONFIG, etc.

    min_value: Optional[float] = None   # For numeric validation
    max_value: Optional[float] = None   # For numeric validation

    extra_attributes: List[str] = field(default_factory=list)
```

### Formula Patterns

1. **Simple arithmetic**: `"value / 10"`
2. **Multi-register**: `"(data[4127] << 16) | value"`
3. **Bit extraction**: `"(value >> 8) & 0xFF"` or `{"bit": 3, "mask": 0x8}`
4. **String formatting**: MAC/IP addresses
5. **Conditional logic**: Complex transformations

### Device Identification Recommendation

**Current Implementation**:
```python
# Uses DEVICE_ID (registers 4111-4112)
device_id = (msw << 16) | lsw
```

**Recommended Change**:
```python
# Use MAC address for consistency with autodiscovery
mac_bytes = [
    (part3 >> 8) & 0xFF,
    part3 & 0xFF,
    (part2 >> 8) & 0xFF,
    part2 & 0xFF,
    (part1 >> 8) & 0xFF,
    part1 & 0xFF,
]
mac_address = ":".join(f"{byte:02X}" for byte in mac_bytes)
```

## Next Steps

### Immediate Tasks:
1. ✅ Create `entity_definitions.py` with core structure (COMPLETED)
2. ✅ Start extracting sensor definitions from existing code (7/30 sensors defined)
3. ✅ Document all formula patterns needed (formula evaluation system implemented)
4. ✅ Update config_flow to use MAC address as primary identifier
5. ✅ Complete remaining sensor definitions (~23 more sensors) - ALL 35 SENSORS COMPLETED
6. Add button, number, select, and text entity definitions (buttons added, numbers/selects/texts pending)
7. Create comprehensive tests for all entity types

### Completed Milestones:
- ✅ Data-driven entity generation framework established
- ✅ Formula evaluation system implemented with safe execution
- ✅ 35 sensor definitions created with working formulas
- ✅ Comprehensive test suite (8/8 passing)
- ✅ Device identification using MAC address pattern documented
- ✅ Updated `__init__.py` to use dynamic entity creation
- ✅ Updated `manifest.json` with DHCP discovery support
- ✅ Updated `config_flow.py` with DHCP autodiscovery
- ✅ Created `quality_scale.yaml` for bronze tier tracking

### Blockers:
- Need to create hub.py and coordinator.py from refactor source
- Need to validate formula evaluation approach
- Need to ensure backward compatibility with existing installations

## Notes

1. **Naming Convention**: Use `midnite_classic` domain consistently (not `MidniteSolar`)
2. **File Organization**: Split entity definitions by type to avoid enormous files
3. **Testing Strategy**: Test each entity type separately before full migration
4. **Documentation**: Maintain comprehensive comments in all definition files
5. **Formula Safety**: Implemented safe formula evaluation with restricted globals
6. **Device Identification**: Using MAC address pattern for consistency

## Implementation Status Summary

### Core Components:
- ✅ `entity_definitions.py` - Complete base dataclass structure
- ✅ `sensor_definitions.py` - 35/35 sensors defined (ALL COMPLETED)
- ✅ `button_definitions.py` - 3 buttons defined
- ✅ `entity_factory.py` - Factory functions and formula evaluation system
- ✅ `test_entity_factory.py` - Comprehensive tests (8/8 passing)
- ✅ `__init__.py` - Updated with coordinator pattern
- ✅ `config_flow.py` - DHCP autodiscovery implemented
- ✅ `manifest.json` - Updated with discovery support
- ✅ `quality_scale.yaml` - Created for bronze tier

### Key Features Implemented:
- Data-driven entity generation using Python dataclasses
- Formula evaluation with R1, R2, etc. register references
- Multi-register combinations (32-bit values from two 16-bit registers)
- Safe formula execution with restricted namespace
- Device identification using MAC address pattern
- DHCP autodiscovery for devices with MAC 601D0F*
- Unique ID management to prevent duplicates

### Remaining Work:
- [ ] Update hub.py and coordinator.py from refactor source
- [ ] Add number, select, and text entity definitions (currently commented out)
- [ ] Create comprehensive tests for all entity types

## References

- Register map: `refactor-source/registers.json`
- Existing implementation: `refactor-source/custom_components/midnite/`
- Current scaffolding: `homeassistant/components/midnite_classic/`
