"""
Factory (manufacturer-specific) code meanings, plus step-by-step checks for common problems.

Manufacturer-specific codes (P1xxx, and B/C/U codes with a 1 or 2 after the letter) mean different things on
different makes. Only meanings that are well established are listed here; anything else still gets a
"look it up" link. Meanings can vary a little by model and year, so the app says so next to them.
"""

FORD = {
    # Engine and emissions
    "P1000": "Self-tests not finished yet since the last time codes were cleared (not a fault)",
    "P1001": "Engine-running self-test couldn't finish",
    "P1100": "Mass airflow (MAF) sensor signal comes and goes",
    "P1101": "Mass airflow (MAF) sensor reading out of range during self-test",
    "P1112": "Intake air temperature sensor signal comes and goes",
    "P1116": "Coolant temperature sensor reading out of range during self-test",
    "P1117": "Coolant temperature sensor signal comes and goes",
    "P1120": "Throttle position sensor reading too low",
    "P1121": "Throttle position sensor doesn't agree with the airflow sensor",
    "P1124": "Throttle position sensor out of range during self-test",
    "P1125": "Throttle position sensor signal comes and goes",
    "P1130": "Front oxygen sensor not switching, fuel adjustment at its limit (bank 1)",
    "P1131": "Front oxygen sensor not switching, reads lean (bank 1)",
    "P1132": "Front oxygen sensor not switching, reads rich (bank 1)",
    "P1150": "Front oxygen sensor not switching, fuel adjustment at its limit (bank 2)",
    "P1151": "Front oxygen sensor not switching, reads lean (bank 2)",
    "P1152": "Front oxygen sensor not switching, reads rich (bank 2)",
    "P1211": "Diesel injection control pressure higher or lower than it should be",
    "P1233": "Fuel pump driver module turned off or not answering",
    "P1235": "Fuel pump control out of range",
    "P1237": "Fuel pump secondary circuit fault",
    "P1260": "Anti-theft (PATS) blocked the engine: key not recognized",
    "P1270": "Engine speed or vehicle speed limiter reached",
    "P1280": "Diesel injection control pressure sensor reading too low",
    "P1281": "Diesel injection control pressure sensor reading too high",
    "P1285": "Cylinder head too hot",
    "P1288": "Cylinder head temperature sensor out of range during self-test",
    "P1289": "Cylinder head temperature sensor circuit reading high",
    "P1290": "Cylinder head temperature sensor circuit reading low",
    "P1299": "Engine overheat protection is active (cylinder head too hot)",
    "P1316": "Diesel injector driver module has its own fault codes stored",
    "P1351": "Ignition diagnostic monitor signal missing",
    "P1400": "EGR pressure sensor (DPFE) circuit reading low",
    "P1401": "EGR pressure sensor (DPFE) circuit reading high",
    "P1405": "EGR pressure sensor (DPFE) upstream hose off or plugged",
    "P1406": "EGR pressure sensor (DPFE) downstream hose off or plugged",
    "P1408": "EGR flow out of range during self-test",
    "P1409": "EGR vacuum regulator solenoid circuit fault",
    "P1450": "Fuel tank vacuum can't build up (EVAP)",
    "P1451": "EVAP canister vent solenoid circuit fault",
    "P1460": "Wide-open-throttle A/C cut-off relay circuit fault",
    "P1464": "A/C request signal out of range during self-test",
    "P1474": "Low-speed cooling fan control circuit fault",
    "P1479": "High-speed cooling fan control circuit fault",
    "P1500": "Vehicle speed sensor signal comes and goes",
    "P1501": "Vehicle speed sensor out of range during self-test",
    "P1504": "Idle air control valve circuit fault",
    "P1505": "Idle air control at its adjustment limit",
    "P1506": "Idle speed higher than it should be",
    "P1507": "Idle speed lower than it should be",
    "P1516": "Intake manifold runner control (bank 1) not working right",
    "P1517": "Intake manifold runner control (bank 2) not working right",
    "P1518": "Intake manifold runner control stuck open",
    "P1549": "Intake manifold tuning valve fault",
    "P1605": "Engine computer memory (keep-alive) test error",
    "P1635": "Tire size or axle ratio setting out of range",
    "P1639": "Vehicle ID (build information) missing or corrupted in the engine computer",
    "P1650": "Power steering pressure switch out of range during self-test",
    "P1651": "Power steering pressure switch signal fault",
    # Transmission
    "P1700": "Transmission fault, transmission in limp mode",
    "P1703": "Brake pedal switch out of range during self-test",
    "P1705": "Transmission range (gear position) sensor out of range during self-test",
    "P1711": "Transmission fluid temperature sensor out of range during self-test",
    "P1714": "Shift solenoid A not working right",
    "P1715": "Shift solenoid B not working right",
    "P1728": "Transmission slipping",
    "P1729": "4x4 low switch fault",
    "P1740": "Torque converter clutch solenoid not working right",
    "P1744": "Torque converter clutch not locking up as it should",
    "P1746": "Transmission pressure control (EPC) solenoid circuit open",
    "P1747": "Transmission pressure control (EPC) solenoid circuit shorted",
    "P1780": "Overdrive cancel switch out of range during self-test",
    "P1781": "4x4 low switch out of range during self-test",
    "P1783": "Transmission too hot",
    # ABS
    "C1095": "ABS pump motor circuit fault",
    "C1096": "ABS pump motor circuit open",
    "C1145": "Right front wheel speed sensor circuit fault",
    "C1155": "Left front wheel speed sensor circuit fault",
    "C1165": "Right rear wheel speed sensor circuit fault",
    "C1175": "Left rear wheel speed sensor circuit fault",
    "C1185": "ABS power relay output circuit fault",
    "C1194": "Left front ABS outlet valve circuit fault",
    "C1198": "Left front ABS inlet valve circuit fault",
    "C1210": "Right front ABS outlet valve circuit fault",
    "C1214": "Right front ABS inlet valve circuit fault",
    "C1222": "Wheel speeds don't match each other",
    "C1233": "Left front wheel speed signal missing",
    "C1234": "Right front wheel speed signal missing",
    "C1235": "Right rear wheel speed signal missing",
    "C1236": "Left rear wheel speed signal missing",
    "C1242": "Left rear ABS outlet valve circuit fault",
    "C1246": "Left rear ABS inlet valve circuit fault",
    "C1250": "Right rear ABS outlet valve circuit fault",
    "C1254": "Right rear ABS inlet valve circuit fault",
    # Body and airbags
    "B1318": "Battery voltage low",
    "B1342": "Module has an internal fault",
    "B1869": "Airbag warning light circuit open",
    "B1870": "Airbag warning light circuit shorted to battery",
    "B1921": "Airbag module ground circuit open",
    "B1932": "Driver airbag circuit open (often the clock spring behind the steering wheel)",
    "B2477": "Module configuration (set-up) fault",
    # Network
    "U1262": "Module network (SCP) communication fault",
    "U1900": "Module network (CAN) communication fault, messages not received",
}

GM = {
    # Engine and emissions
    "P1101": "Intake airflow system performance (air leak or airflow sensor problem)",
    "P1125": "Accelerator pedal position system fault",
    "P1133": "Front oxygen sensor not switching enough (bank 1)",
    "P1134": "Front oxygen sensor switching too slowly (bank 1)",
    "P1153": "Front oxygen sensor not switching enough (bank 2)",
    "P1154": "Front oxygen sensor switching too slowly (bank 2)",
    "P1258": "Engine overheating, protection mode active",
    "P1345": "Crankshaft and camshaft sensor signals don't line up (timing)",
    "P1351": "Ignition control circuit voltage high",
    "P1361": "Ignition control circuit voltage low",
    "P1380": "Misfire detected, rough-road data from the ABS not available",
    "P1381": "Misfire detected, no data from the ABS computer",
    "P1406": "EGR valve position sensor circuit fault",
    "P1415": "Secondary air injection system fault (bank 1)",
    "P1416": "Secondary air injection system fault (bank 2)",
    "P1441": "EVAP system flow when it should be off (purge valve leaking)",
    "P1508": "Idle speed too low, idle air control not responding",
    "P1509": "Idle speed too high, idle air control not responding",
    "P1516": "Electronic throttle body position doesn't match what was commanded",
    "P1626": "Anti-theft fuel-enable signal not received",
    "P1630": "Anti-theft system is in learn mode",
    "P1631": "Anti-theft start-enable signal not correct",
    "P1635": "5-volt sensor supply circuit fault",
    "P1639": "Second 5-volt sensor supply circuit fault",
    "P1682": "Ignition switch power circuit 2 fault",
    # Transmission
    "P1810": "Transmission fluid pressure switch circuit fault",
    "P1860": "Torque converter clutch solenoid circuit fault",
    "P1870": "Transmission slipping (worn internal part)",
    # ABS
    "C0110": "ABS pump motor circuit fault",
    "C0121": "ABS valve relay circuit fault",
    "C0161": "ABS brake switch circuit fault",
    "C0242": "Engine computer reported a traction control fault",
    "C0265": "ABS module relay circuit fault",
    "C0267": "ABS pump motor circuit open or shorted",
    "C0550": "ABS module internal fault",
    "C0561": "ABS system turned off because of a stored fault",
    "C0896": "ABS module supply voltage out of range",
    # Body and airbags
    "B0051": "Airbag deployment commanded (crash data stored, module usually needs replacing)",
    "B1000": "Module has an internal fault",
    "B1001": "Module options set-up fault",
    # Network (Class 2, older GM)
    "U1000": "Module network (Class 2) communication fault",
    "U1016": "Lost communication with the engine computer",
    "U1041": "Lost communication with the ABS module",
    "U1064": "Lost communication with the body control module",
    "U1088": "Lost communication with the airbag module",
    "U1300": "Module network (Class 2) wire shorted to ground",
    "U1301": "Module network (Class 2) wire shorted to battery voltage",
}

FAMILY_OF_MAKE = {
    "ford": "ford", "lincoln": "ford", "mercury": "ford",
    "chevrolet": "gm", "chevy": "gm", "gmc": "gm", "cadillac": "gm", "buick": "gm", "pontiac": "gm",
    "oldsmobile": "gm", "saturn": "gm", "hummer": "gm", "gm": "gm",
}
TABLES = {"ford": (FORD, "Ford"), "gm": (GM, "GM")}


def family(make):
    return FAMILY_OF_MAKE.get((make or "").strip().lower())


def lookup(code, make):
    """-> (meaning, "Ford"/"GM") for a manufacturer-specific code on this make, else (None, None)."""
    fam = family(make)
    if not fam:
        return None, None
    table, label = TABLES[fam]
    meaning = table.get(code.upper().split("-")[0])
    return (meaning, label) if meaning else (None, None)


# --- How to check it: steps you can do with basic tools ---------------------------------------------
CHECKS = {
    "misfire": [
        "Look at Live data with the engine idling. Note which cylinder number the code names.",
        "Pull that cylinder's spark plug. Look for oil, heavy carbon, a cracked tip or a wide gap.",
        "Swap that cylinder's ignition coil with a neighbor's, clear the code and drive. If the misfire moves "
        "to the other cylinder, the coil is bad.",
        "If it stays, swap the spark plug the same way. If it still stays, have the injector and compression "
        "checked.",
    ],
    "lean": [
        "With the engine running, listen around the intake for a hiss (vacuum leak). Check the PCV hose and "
        "the big intake boot after the air filter for cracks.",
        "Check the air filter, and clean the airflow (MAF) sensor with MAF cleaner spray only.",
        "In Live data, watch the fuel trims: above +10% at idle that drops at 2,500 rpm points to a vacuum "
        "leak; high at both points to weak fuel delivery.",
        "If fuel delivery is suspect, have the fuel pressure tested.",
    ],
    "rich": [
        "Check the air filter isn't clogged.",
        "Clean the airflow (MAF) sensor with MAF cleaner spray.",
        "In Live data, check the coolant temperature reads close to normal (about 190-220 °F) once warm. "
        "A sensor stuck cold makes the engine run rich.",
        "Have the fuel pressure checked for a regulator or leaking injector.",
    ],
    "cat": [
        "Fix any misfire or fuel-trim codes first. They cause this code and ruin new converters.",
        "Check for exhaust leaks ahead of the rear oxygen sensor (black soot marks, ticking sound).",
        "In Live data, the rear oxygen sensor should stay fairly steady when warm. If it switches as fast "
        "as the front one, the converter is worn out.",
    ],
    "evap": [
        "Check the gas cap: tighten until it clicks, and look at the rubber seal for cracks. A new cap is "
        "cheap and fixes many of these.",
        "Clear the code and drive for a few days. It can take several drives to re-test.",
        "If it comes back, look over the hoses near the charcoal canister and fuel tank for cracks.",
        "Small leaks are found fastest with a smoke test at a shop.",
    ],
    "thermostat": [
        "With the engine cold, check the coolant level.",
        "Drive 15 minutes and watch coolant temperature in Live data. If it stays below about 180 °F, the "
        "thermostat is likely stuck open.",
        "Replace the thermostat (and gasket). It's usually an inexpensive part.",
    ],
    "vvt": [
        "Check the engine oil level and condition first. Low or dirty oil causes most of these.",
        "Change the oil and filter with the right grade if it's due.",
        "If the code returns, check the oil-control (VVT) solenoid's connector, then test or replace the solenoid.",
    ],
    "timing": [
        "Don't keep driving hard: timing problems can damage the engine.",
        "Check the oil level and condition.",
        "Check the crank and cam sensor connectors and wiring.",
        "If those are fine, have the timing chain or belt checked for stretch or a jumped tooth.",
    ],
    "egr": [
        "Check the vacuum hoses and electrical connector at the EGR valve.",
        "Remove the EGR valve and look for heavy carbon. Clean the valve and passages.",
        "On Fords with a DPFE sensor (small sensor with two rubber hoses), check both hoses for cracks or "
        "being swapped. The sensor itself often fails and is inexpensive.",
    ],
    "idle": [
        "Clean the throttle body with throttle-body cleaner (engine off, key out).",
        "Look for vacuum leaks around the intake.",
        "If it has an idle air control valve, check its connector and clean or replace it.",
    ],
    "o2heater": [
        "Check the fuse for the oxygen sensor heaters (see the owner's manual fuse chart).",
        "Look at the sensor wiring under the vehicle for melted or chafed spots near the exhaust.",
        "If the wiring and fuse are fine, replace the oxygen sensor the code names.",
    ],
    "voltage": [
        "Check the battery terminals and ground straps are clean and tight.",
        "Look at Battery on the Vehicle page with the engine off: under about 12.4 volts means a weak or "
        "discharged battery.",
        "With the engine running it should read about 13.5-14.7 volts. Lower points to the alternator.",
        "Most parts stores test the battery and alternator for free.",
    ],
    "crankcam": [
        "Check the sensor's connector for corrosion or a loose fit, and the wiring for rubbing.",
        "Clear the code. If it comes back right away, the sensor is likely bad.",
        "On GM trucks, a crank relearn may be needed after replacing the crank sensor.",
    ],
    "maf": [
        "Check the air filter and the intake boot between the sensor and the engine for cracks.",
        "Clean the airflow (MAF) sensor with MAF cleaner spray only. Let it dry before starting.",
        "If the code returns, check the connector, then replace the sensor.",
    ],
    "network": [
        "Check the battery is charged and the terminals are tight. Low voltage causes many of these.",
        "Check the fuses for the module that stopped talking.",
        "Clear the codes and scan again. If the same module is missing, check its connector and power.",
    ],
    "fuelpressure": [
        "Listen for the fuel pump running for 2 seconds when you turn the key to ON.",
        "Replace the fuel filter if it's serviceable and overdue.",
        "Have the fuel pressure tested with a gauge to confirm a weak pump or bad regulator.",
    ],
    "boost": [
        "With the engine off, check the intercooler hoses and clamps for cracks or looseness.",
        "Look for oil or soot around hose joints, a sign of a boost leak.",
        "Have the turbo and wastegate checked if the hoses are fine.",
    ],
    "postcat": [
        "Fix any front oxygen sensor or fuel-trim codes first.",
        "Check for exhaust leaks near the rear oxygen sensor.",
        "If those are fine, replace the rear oxygen sensor.",
    ],
    "wheelspeed": [
        "Note which wheel the code names. Look at that wheel's sensor wire for damage near the hub.",
        "Unplug the sensor, check for corrosion, and plug it back in firmly.",
        "Remove the sensor and clean any rust or metal debris from its tip.",
        "With Live data on a test drive, a sensor that drops to 0 while the others read speed is bad. A worn "
        "wheel bearing with a built-in sensor can also cause it.",
    ],
    "pats": [
        "Try a different programmed key. A key with a damaged chip causes this.",
        "Keep other keys, fobs and metal keychains away from the ignition key.",
        "If you have two working keys you can add keys yourself (see the owner's manual). Otherwise a "
        "locksmith or the dealer can program one.",
    ],
    "gmtheft": [
        "Turn the key to ON and leave it for about 10 minutes until the security light stops flashing, then "
        "turn it off for 5 seconds and start (the GM relearn). If that doesn't work, do it three times "
        "(30 minutes).",
        "Check the battery is fully charged before trying.",
        "If it keeps happening, the ignition lock cylinder's sensor is often at fault.",
    ],
    "dpfe": [
        "Find the DPFE sensor (small sensor with two rubber hoses going to the exhaust/EGR tube).",
        "Check both hoses for cracks, melting or being off. Make sure they aren't swapped.",
        "Replace the DPFE sensor if the hoses are fine. It's a common, inexpensive part on Fords.",
    ],
    "transmission": [
        "Check the transmission fluid level and smell (with the engine warm and running on most trucks). "
        "Burnt-smelling or dark fluid means wear.",
        "Look for other transmission codes in this list. They usually point to the real problem.",
        "Check the connector on the side of the transmission for corrosion.",
        "Slipping usually needs a transmission shop.",
    ],
    "throttle": [
        "Clean the throttle body (engine off, key out).",
        "Check the throttle body and accelerator pedal connectors.",
        "If the code returns, the electronic throttle body usually needs replacing.",
    ],
}

_CHECK_CODES = {  # codes that mean the same thing everywhere, or are listed for one make below
    "transmission": ("P0730", "P0731", "P0732", "P0733", "P0734", "P0741", "P0218"),
    "throttle": ("P2135", "P2101", "P2119", "P0121", "P0122", "P0123"),
}
_CHECK_CODES_BY_FAMILY = {
    "ford": {
        "pats": ("P1260",),
        "dpfe": ("P1400", "P1401", "P1405", "P1406"),
        "transmission": ("P1700", "P1728", "P1744", "P1783"),
        "lean": ("P1131", "P1151"),
        "rich": ("P1132", "P1152"),
        "maf": ("P1100", "P1101"),
        "egr": ("P1408", "P1409"),
        "idle": ("P1504", "P1505", "P1506", "P1507"),
        "voltage": ("B1318",),
        "wheelspeed": ("C1145", "C1155", "C1165", "C1175", "C1222", "C1233", "C1234", "C1235", "C1236"),
        "network": ("U1262", "U1900"),
    },
    "gm": {
        "gmtheft": ("P1626", "P1630", "P1631"),
        "transmission": ("P1870",),
        "throttle": ("P1516", "P1125"),
        "maf": ("P1101",),
        "egr": ("P1406",),
        "idle": ("P1508", "P1509"),
        "voltage": ("C0896",),
        "network": ("U1000", "U1016", "U1041", "U1064", "U1088"),
        "crankcam": ("P1345",),
    },
}


def check_steps(code, cause_key="", make=""):
    """Steps to check a problem. cause_key comes from dtc_database's own grouping of generic codes."""
    c = code.upper().split("-")[0]
    groups = [_CHECK_CODES_BY_FAMILY.get(family(make), {}), _CHECK_CODES]
    for table in groups:
        for key, codes in table.items():
            if c in codes:
                return CHECKS[key]
    return CHECKS.get(cause_key, [])
