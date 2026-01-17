"""Constants for the Midnite Classic integration."""

DOMAIN = "midnite_classic"
DEFAULT_PORT = 502
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 15

# Device types mapping (from UNIT_ID register)
DEVICE_TYPES = {
    0x00: "Classic CC",
    0x01: "Classic LV",
    0x02: "Classic 250",
    0x03: "Classic 150",
    0x04: "Classic 175",
    0x05: "Classic 200",
    0x06: "Classic 250SE",
    0x07: "Classic 150SE",
    0x08: "Classic 175SE",
    0x09: "Classic 200SE",
    150: "Classic 150",
    200: "Classic 200",
    250: "Classic 250",
    251: "Classic 250 KS (120V battery capability)",
}

# Charge stage mappings (from register 4120 MSB)
CHARGE_STAGES = {
    0: "Resting",
    3: "Absorb",
    4: "BulkMPPT",
    5: "Float",
    6: "FloatMppt",
    7: "Equalize",
    10: "HyperVoc",
    18: "EQ MPPT",
}

# Internal state mappings (from register 4120 LSB)
INTERNAL_STATES = {
    0: "Resting",
    1: "Waking/Starting (state 1)",
    2: "Waking/Starting (state 2)",
    3: "MPPT / Regulating Voltage (state 3)",
    4: "MPPT / Regulating Voltage (state 4)",
    6: "MPPT / Regulating Voltage (state 6)",
}

# Rest reasons from register 4275
REST_REASONS = {
    1: "Anti-Click. Not enough power available (Wake Up)",
    2: "Insane Ibatt Measurement (Wake Up)",
    3: "Negative Current (load on PV input?) (Wake Up)",
    4: "PV Input Voltage lower than Battery V (Vreg state)",
    5: "Too low of power out and Vbatt below set point for > 90 seconds",
    6: "FET temperature too high (Cover is on maybe?)",
    7: "Ground Fault Detected",
    8: "Arc Fault Detected",
    9: "Too much negative current while operating (backfeed from battery out of PV input)",
    10: "Battery is less than 8.0 Volts",
    11: "PV input is available but V is rising too slowly. Low Light or bad connection (Solar mode)",
    12: "Voc has gone down from last Voc or low light. Re-check (Solar mode)",
    13: "Voc has gone up from last Voc enough to be suspicious. Re-check (Solar mode)",
    14: "Same as 11",
    15: "Same as 12",
    16: "MPPT MODE is OFF (Usually because user turned it off)",
    17: "PV input is higher than operation range (too high for 150V Classic)",
    18: "PV input is higher than operation range (too high for 200V Classic)",
    19: "PV input is higher than operation range (too high for 250V or 250KS)",
    22: "Average Battery Voltage is too high above set point",
    25: "Battery Voltage too high of Overshoot (small battery or bad cable?)",
    26: "Mode changed while running OR Vabsorb raised more than 10.0 Volts at once OR Nominal Vbatt changed by modbus command AND MpptMode was ON when changed",
    27: "Bridge center == 1023 (R132 might have been stuffed) This turns MPPT Mode to OFF",
    28: "NOT Resting but RELAY is not engaged for some reason",
    29: "ON/OFF stays off because WIND GRAPH is illegal (current step is set for > 100 amps)",
    30: "PkAmpsOverLimit... Software detected too high of PEAK output current",
    31: "AD1CH.IbattMinus > 900 Peak negative battery current > 90.0 amps (Classic 250)",
    32: "Aux 2 input commanded Classic off for HI or LO (Aux2Function == 15 or 16)",
    33: "OCP in a mode other than Solar or PV-Uset",
    34: "AD1CH.IbattMinus > 900 Peak negative battery current > 90.0 amps (Classic 150, 200)",
    35: "Battery voltage is less than Low Battery Disconnect (LBD) Typically Vbatt is less than 8.5 volts",
}

# Force flag bit mappings (from register 4160)
FORCE_FLAGS = {
    "ForceEEpromUpdate": 2,  # Bit position
    "ForceEEpromInitRead": 3,
    "ForceResetInfoFlags": 4,
    "ForceFloat": 5,
    "ForceBulk": 6,
    "ForceEqualize": 7,
    "ForceNite": 8,
    "ResetAeqCounts": 13,
    "ForceSweep": 16,
    "ResetFlags": 20,  # Bit position
    "ForceResetFaults": 29,
}

# MPPT mode mappings (from register 4164)
MPPT_MODES = {
    0x0001: "PV_Uset",
    0x0003: "DYNAMIC",
    0x0005: "WIND_TRACK",
    0x0007: "RESERVED",
    0x0009: "Legacy P&O",
    0x000B: "SOLAR",
    0x000D: "HYDRO",
    0x000F: "RESERVED",
}

# IP settings flags (from register 20481)
IP_SETTINGS_FLAGS = {
    "DHCP": 0,
    "Web_Access": 1,
}

# Auxiliary function mappings for AUX_1_AND_2_FUNCTION register
AUX1_FUNCTIONS = [
    "Off",
    "Auto",
    "On",
    "HiAbs",
    "LoAbs",
    "WasteNot",
    "PVHiAbs",
    "PVLoAbs",
]

AUX2_FUNCTIONS = [
    "Off",
    "Auto",
    "On",
    "HiAbs",
    "LoAbs",
    "WasteNot",
    "PWM",
    "PVHiAbs",
]
