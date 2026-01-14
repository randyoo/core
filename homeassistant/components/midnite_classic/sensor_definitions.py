"""Sensor entity definitions for midnite_classic integration."""

from __future__ import annotations

from .entity_definitions import SensorDefinition

SENSOR_DEFINITIONS = [
    # Basic status sensors
    SensorDefinition(
        key="battery_voltage",
        name="Battery Voltage",
        register_group="status",
        register_address=4115,
        formula="value / 10",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
    ),
    SensorDefinition(
        key="pv_voltage",
        name="PV Voltage",
        register_group="status",
        register_address=4116,
        formula="value / 10",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
    ),
    SensorDefinition(
        key="battery_current",
        name="Battery Current",
        register_group="status",
        register_address=4117,
        formula="""
            current_value = value / 10.0
            if current_value > 32767:
                current_value = current_value - 65536
            return current_value if abs(current_value) <= 200 else None
        """,
        device_class="current",
        state_class="measurement",
        unit="A",
        precision=1,
    ),
    SensorDefinition(
        key="power_output",
        name="Power Output",
        register_group="status",
        register_address=4119,
        formula="value",
        device_class="power",
        state_class="measurement",
        unit="W",
    ),
    # Temperature sensors
    SensorDefinition(
        key="battery_temperature",
        name="Battery Temperature",
        register_group="temperatures",
        register_address=4132,
        formula="value / 10",
        device_class="temperature",
        state_class="measurement",
        unit="°C",
        precision=1,
    ),
    SensorDefinition(
        key="fet_temperature",
        name="FET Temperature",
        register_group="temperatures",
        register_address=4133,
        formula="value / 10",
        device_class="temperature",
        state_class="measurement",
        unit="°C",
        precision=1,
        entity_category="diagnostic",
    ),
    # Energy sensors
    SensorDefinition(
        key="daily_energy",
        name="Daily Energy",
        register_group="status",
        register_address=4118,
        formula="value / 10.0",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        precision=1,
    ),
    # Device info sensors
    SensorDefinition(
        key="device_type",
        name="Device Type",
        register_group="device_info",
        register_address=4101,
        formula="""
            device_value = value & 0xFF  # Get LSB (unit type)
            from .const import DEVICE_TYPES
            return DEVICE_TYPES.get(device_value, f"Unknown ({device_value})")
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="charge_stage",
        name="Charge Stage",
        register_group="status",
        register_address=4120,
        formula="""
            from .const import CHARGE_STAGES
            charge_stage_value = (value >> 8) & 0xFF
            return CHARGE_STAGES.get(charge_stage_value, f"Unknown ({charge_stage_value})")
        """,
        device_class="enum",
    ),
    SensorDefinition(
        key="internal_state",
        name="Internal State",
        register_group="status",
        register_address=4120,
        formula="""
            from .const import INTERNAL_STATES, REST_REASONS
            internal_state_value = value & 0xFF
            internal_state = INTERNAL_STATES.get(internal_state_value, f"Unknown ({internal_state_value})")
            return internal_state
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="rest_reason",
        name="Rest Reason",
        register_group="status",
        register_address=4120,
        formula="""
            from .const import INTERNAL_STATES, REST_REASONS
            internal_state_value = value & 0xFF
            internal_state = INTERNAL_STATES.get(internal_state_value, f"Unknown ({internal_state_value})")
            if internal_state == "Resting":
                return "Resting"
            else:
                return "Not resting"
        """,
        entity_category="diagnostic",
    ),
    # Temperature sensors
    SensorDefinition(
        key="pcb_temperature",
        name="PCB Temperature",
        register_group="temperatures",
        register_address=4134,
        formula="""
            temp_value = value / 10.0
            if value > 32767:
                temp_value = (value - 65536) / 10.0
            return temp_value if -50 <= temp_value <= 150 else None
        """,
        device_class="temperature",
        state_class="measurement",
        unit="°C",
        precision=1,
        entity_category="diagnostic",
    ),
    # Energy sensors
    SensorDefinition(
        key="lifetime_energy",
        name="Lifetime Energy",
        register_group="energy",
        register_address=4126,
        secondary_registers=[4127],
        formula="""
            high_value = data[4127]
            value = (high_value << 16) | value
            return value / 10.0
        """,
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        precision=1,
    ),
    SensorDefinition(
        key="lifetime_amp_hours",
        name="Lifetime Amp-Hours",
        register_group="energy",
        register_address=4128,
        secondary_registers=[4129],
        formula="""
            high_value = data[4129]
            value = (high_value << 16) | value
            return float(value) / 10.0
        """,
        state_class="total_increasing",
        unit="Ah",
        precision=1,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="daily_amp_hours",
        name="Daily Amp-Hours",
        register_group="energy",
        register_address=4125,
        formula="float(value)",
        state_class="total_increasing",
        unit="Ah",
        precision=0,
        entity_category="diagnostic",
    ),
    # Current sensors
    SensorDefinition(
        key="pv_input_current",
        name="PV Input Current",
        register_group="status",
        register_address=4121,
        formula="""
            current_value = value / 10.0
            if current_value > 32767:
                current_value = current_value - 65536
            return current_value if abs(current_value) <= 100 else None
        """,
        device_class="current",
        state_class="measurement",
        unit="A",
        precision=1,
        entity_category="diagnostic",
    ),
    # Voltage sensors
    SensorDefinition(
        key="voc_measured",
        name="Last Measured VOC",
        register_group="status",
        register_address=4122,
        formula="value / 10.0",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="highest_input_voltage",
        name="Highest Input Voltage",
        register_group="status",
        register_address=4123,
        formula="value / 10.0",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
        entity_category="diagnostic",
    ),
    # Time sensors
    SensorDefinition(
        key="float_time_today",
        name="Float Time Today",
        register_group="time_settings",
        register_address=4138,
        formula="value / 60.0",
        device_class="duration",
        state_class="measurement",
        unit="minutes",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="absorb_time_remaining",
        name="Absorb Time Remaining",
        register_group="time_settings",
        register_address=4139,
        formula="value / 60.0",
        device_class="duration",
        state_class="measurement",
        unit="minutes",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="equalize_time_remaining",
        name="Equalize Time Remaining",
        register_group="time_settings",
        register_address=4143,
        formula="value / 60.0",
        device_class="duration",
        state_class="measurement",
        unit="minutes",
        precision=0,
        entity_category="diagnostic",
    ),
    # Network sensors
    SensorDefinition(
        key="mac_address",
        name="MAC Address",
        register_group="device_info",
        register_address=4106,
        secondary_registers=[4107, 4108],
        formula="""
            part2 = data[4107]
            part3 = data[4108]
            mac_bytes = [
                (part3 >> 8) & 0xFF,
                part3 & 0xFF,
                (part2 >> 8) & 0xFF,
                part2 & 0xFF,
                (value >> 8) & 0xFF,
                value & 0xFF,
            ]
            return ":".join(f"{byte:02X}" for byte in mac_bytes)
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="ip_address",
        name="IP Address",
        register_group="network",
        register_address=20482,
        secondary_registers=[20483],
        formula="""
            part2 = data[20483]
            octets = []
            def get_octets(reg_value):
                return [(reg_value >> 8) & 0xFF, reg_value & 0xFF]
            octets.extend(get_octets(part2))
            octets.extend(get_octets(value))
            return ".".join(str(octet) for octet in reversed(octets[:4]))
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="gateway_address",
        name="Gateway Address",
        register_group="network",
        register_address=20484,
        secondary_registers=[20485],
        formula="""
            part2 = data[20485]
            octets = []
            def get_octets(reg_value):
                return [(reg_value >> 8) & 0xFF, reg_value & 0xFF]
            octets.extend(get_octets(part2))
            octets.extend(get_octets(value))
            return ".".join(str(octet) for octet in reversed(octets[:4]))
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="subnet_mask",
        name="Subnet Mask",
        register_group="network",
        register_address=20486,
        secondary_registers=[20487],
        formula="""
            part2 = data[20487]
            octets = []
            def get_octets(reg_value):
                return [(reg_value >> 8) & 0xFF, reg_value & 0xFF]
            octets.extend(get_octets(part2))
            octets.extend(get_octets(value))
            return ".".join(str(octet) for octet in reversed(octets[:4]))
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="dns1",
        name="DNS Server 1",
        register_group="network",
        register_address=20488,
        secondary_registers=[20489],
        formula="""
            part2 = data[20489]
            octets = []
            def get_octets(reg_value):
                return [(reg_value >> 8) & 0xFF, reg_value & 0xFF]
            octets.extend(get_octets(part2))
            octets.extend(get_octets(value))
            return ".".join(str(octet) for octet in reversed(octets[:4]))
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="dns2",
        name="DNS Server 2",
        register_group="network",
        register_address=20490,
        secondary_registers=[20491],
        formula="""
            part2 = data[20491]
            octets = []
            def get_octets(reg_value):
                return [(reg_value >> 8) & 0xFF, reg_value & 0xFF]
            octets.extend(get_octets(part2))
            octets.extend(get_octets(value))
            return ".".join(str(octet) for octet in reversed(octets[:4]))
        """,
        entity_category="diagnostic",
    ),
    # Diagnostic sensors
    SensorDefinition(
        key="status_roll",
        name="Status Roll",
        register_group="status",
        register_address=4113,
        formula="(value >> 12) + (value & 0x0FFF)",
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="restart_time",
        name="Restart Time",
        register_group="status",
        register_address=4114,
        formula="value",
        device_class="duration",
        state_class="measurement",
        unit="ms",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="match_point_shadow",
        name="Match Point Shadow",
        register_group="status",
        register_address=4124,
        formula="value",
        entity_category="diagnostic",
    ),
    # Settings sensors
    SensorDefinition(
        key="logging_interval",
        name="Logging Interval",
        register_group="settings",
        register_address=4136,
        formula="value",
        device_class="duration",
        state_class="measurement",
        unit="seconds",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="sliding_current_limit",
        name="Sliding Current Limit",
        register_group="settings",
        register_address=4152,
        formula="value / 10.0",
        device_class="current",
        state_class="measurement",
        unit="A",
        precision=1,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="modbus_port",
        name="Modbus Port",
        register_group="settings",
        register_address=4137,
        formula="value",
        entity_category="diagnostic",
    ),
]

# Total: 35 sensors defined
