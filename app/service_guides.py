"""
The repair database the Service page searches: procedures you can do by hand, with no scan-tool commands.

Each guide: title, family ("ford", "gm" or None for most vehicles), applies (which vehicles),
needs (tools), steps, and an optional note (when a shop or scan tool is needed instead).
"""

from dtc_database import mentions

GUIDES = [
    {
        "title": "Engine computer reset (Ford keep-alive memory)",
        "family": "ford",
        "applies": "Older Ford, Lincoln and Mercury vehicles (about 1996-2010). Clears learned idle, fuel and "
                   "shift settings",
        "needs": "A wrench for the battery terminal",
        "steps": [
            "Turn everything off and take the key out.",
            "Disconnect the negative (black) battery cable and leave it off for at least 5 minutes.",
            "Reconnect it tightly.",
            "Start the engine and let it idle for 2 minutes with the A/C off, then 1 minute with the A/C on.",
            "Drive about 10 miles with normal city and highway driving so it relearns.",
        ],
        "note": "Your radio presets and clock may reset. The smog-check self-tests also reset, so don't do this "
                "right before an emissions test.",
    },
    {
        "title": "Oil-life reset (GM, pedal method)",
        "family": "gm",
        "applies": "Many GM cars and trucks from about 1999-2008 with an oil-life light or message",
        "needs": "Nothing",
        "steps": [
            "Turn the key to ON with the engine off.",
            "Within 5 seconds, press the accelerator slowly all the way down and let it up, 3 times.",
            "The oil light or message should flash and go out. Turn the key OFF.",
            "Start the engine to check the light stays off. If not, try again.",
        ],
        "note": "Newer GM vehicles reset it from the dash menu (Vehicle Information or Oil Life, then hold the "
                "select button).",
    },
    {
        "title": "Tire pressure sensor relearn (GM, key fob method)",
        "family": "gm",
        "applies": "Most GM vehicles from about 2007-2016 with tire pressure monitoring, after rotating tires "
                   "or replacing a sensor",
        "needs": "A TPMS activation tool (about $20-30), or a tire gauge to let air out",
        "steps": [
            "Set the parking brake and turn the key to ON with the engine off.",
            "Press and hold LOCK and UNLOCK on the key fob together until the horn chirps twice (about 5-10 "
            "seconds). On some, use the dash menu's Tire Learn option instead.",
            "Starting at the left front tire, hold the tool against the tire by the valve stem and press it "
            "(or let air out until the horn chirps).",
            "Do the same at the right front, then the right rear, then the left rear. The horn chirps after "
            "each one.",
            "After the last tire the horn chirps twice. Turn the key OFF and set all tires to the pressure "
            "on the door sticker.",
        ],
        "note": "",
    },
    {
        "title": "Idle relearn after cleaning the throttle body",
        "family": None,
        "applies": "Most vehicles, after cleaning the throttle body or disconnecting the battery",
        "needs": "Nothing",
        "steps": [
            "Turn off the A/C, lights and other loads.",
            "Turn the key to ON for 30 seconds without starting.",
            "Start the engine and let it idle without touching the pedal for about 3-5 minutes, until the "
            "idle settles.",
            "Drive normally. The idle may be a little uneven for the first few drives.",
        ],
        "note": "If the idle stays wrong after a few drives, some vehicles need a scan tool's idle relearn.",
    },
    {
        "title": "Bleed the brakes (manual method, with ABS)",
        "family": None,
        "applies": "Most vehicles with ABS, including 1999-2007 Silverado/Sierra and 1999-2007 Ford Super "
                   "Duty, when the ABS unit itself was not opened or run dry",
        "needs": "A helper, a box-end wrench, clear hose and a bottle, and fresh brake fluid of the type on the "
                 "cap (usually DOT 3)",
        "steps": [
            "Fill the master cylinder. Keep it from going empty the whole time, or air gets into the ABS unit.",
            "Start at the wheel farthest from the master cylinder: right rear, then left rear, then right front, "
            "then left front.",
            "Put the hose on the bleeder screw and into the bottle with some fluid in it.",
            "Have your helper press the brake pedal and hold it down. Open the bleeder about a quarter turn, "
            "let fluid and air out, then close it before your helper lets the pedal up.",
            "Repeat until the fluid comes out with no bubbles, then move to the next wheel.",
            "Top up the master cylinder and check the pedal is firm before driving. Test the brakes gently at "
            "low speed first.",
        ],
        "note": "If the pedal stays soft, or the ABS unit was replaced, opened or run dry, air is trapped inside it. "
                "That needs the ABS valves cycled by a scan tool with an 'automated bleed' function. A shop "
                "can do it, or a bidirectional scanner (about $100-200) can. Don't drive with a soft pedal.",
    },
    {
        "title": "Crankshaft position relearn (GM)",
        "family": "gm",
        "applies": "GM vehicles after replacing the crank sensor, engine computer or timing parts, or with code "
                   "P0315",
        "needs": "A scan tool with GM 'CKP variation learn' (this app can't do it)",
        "steps": [
            "Most GM trucks only need this if code P0315 sets, or a misfire code appears after the repair.",
            "A shop or a bidirectional scanner runs the relearn: the engine is warmed up and revved to a set "
            "speed with the brake held.",
            "Until it's done, the engine runs fine but misfire detection is limited.",
        ],
        "note": "",
    },
    {
        "title": "Replace a car battery",
        "family": None,
        "applies": "Most vehicles, when the battery is weak, dead or won't hold a charge",
        "needs": "A new battery of the right size, a wrench (often 10 mm), gloves and eye protection",
        "steps": [
            "Turn everything off and take the key out. Radio presets and some settings may reset.",
            "Disconnect the negative (-) cable first, then the positive (+) cable.",
            "Remove the hold-down bracket and lift the battery out. It's heavy, so keep it level.",
            "Clean any white or green buildup off the cable ends.",
            "Set the new battery in and tighten the hold-down so it can't move.",
            "Connect the positive (+) cable first, then the negative (-) cable, and start the engine.",
        ],
        "note": "Some newer vehicles need the new battery registered with a scan tool, or the battery may sit under a "
                "seat or in the trunk. Check the owner's manual. Recycle the old battery where you buy the new one.",
    },
    {
        "title": "Jump-start a dead battery",
        "family": None,
        "applies": "Most 12-volt vehicles that won't start because the battery is dead",
        "needs": "Jumper cables and a second vehicle with a good battery, or a jump pack",
        "steps": [
            "Park the vehicles close without touching, and turn both off.",
            "Connect red to the dead battery's positive (+), then red to the good battery's positive (+).",
            "Connect black to the good battery's negative (-), then black to bare metal on the dead vehicle's engine, "
            "away from the battery.",
            "Start the good vehicle and let it run for a few minutes, then start the dead one.",
            "Remove the cables in the reverse order, without letting the clamps touch.",
            "Drive for at least 20 minutes, then test the battery. It may still need replacing.",
        ],
        "note": "Don't jump a battery that's cracked, leaking or frozen. Check the owner's manual first, since hybrids "
                "and some newer vehicles have their own jump-start points and rules.",
    },
    {
        "title": "Find out why the battery won't charge (alternator)",
        "family": None,
        "applies": "Battery light on, dim lights or a battery that keeps dying, which can mean a bad alternator",
        "needs": "This app's Battery test, and a wrench for the battery cables",
        "steps": [
            "With the engine off, check that the battery cables are clean and tight.",
            "Look at the belt that turns the alternator. Replace it if it's cracked, loose or missing.",
            "Run the Battery test in this app. With the engine running it should read about 13.4 to 14.9 volts.",
            "If it's low even with a good belt and cables, have the alternator tested. Many parts stores do this free.",
        ],
        "note": "",
    },
    {
        "title": "Replace the engine air filter",
        "family": None,
        "applies": "Most vehicles, for poor mileage or sluggish power, or as routine maintenance",
        "needs": "The right filter for your engine, and usually a screwdriver or nothing at all",
        "steps": [
            "Find the air box, the big plastic box with a large hose going to the engine.",
            "Undo its clips or screws and lift the cover. Don't strain the sensor wires or hoses attached to it.",
            "Note which way the old filter sits, then lift it out.",
            "Wipe out any leaves or dirt, and drop in the new filter the same way.",
            "Close the cover so it seals all the way around.",
        ],
        "note": "",
    },
    {
        "title": "Clean a mass air flow (MAF) sensor",
        "family": None,
        "applies": "Rough idle, hesitation or lean codes like P0171 and P0101 on vehicles with a MAF sensor",
        "needs": "Spray cleaner made for MAF sensors, and usually a screwdriver",
        "steps": [
            "With the engine off, unplug the sensor. It's in the air intake tube, right after the air filter.",
            "Remove its two screws and lift it out gently.",
            "Spray the thin wires or plate with MAF cleaner. Never touch them, not even with a brush.",
            "Let it dry completely, at least 10 minutes.",
            "Put it back, plug it in, and check the intake hoses for cracks while you're there.",
        ],
        "note": "Use only MAF cleaner. Brake or carburetor cleaner can ruin the sensor.",
    },
    {
        "title": "Replace spark plugs",
        "family": None,
        "applies": "Misfires, rough running or routine maintenance on gasoline engines",
        "needs": "The right plugs for your engine, a ratchet, a spark plug socket and extension, and a torque wrench",
        "steps": [
            "Work on a cold engine, one plug at a time so the wires or coils don't get mixed up.",
            "Remove the coil or plug wire, and blow any dirt out of the plug well so it can't fall in.",
            "Unscrew the old plug. Oil, heavy carbon or damage can point to another problem.",
            "Check the new plug's gap against your engine's spec.",
            "Start the new plug by hand so it can't cross-thread, then tighten it to the spec with a torque wrench.",
            "Refit the coil or wire and repeat. Then start the engine and check that it runs smoothly.",
        ],
        "note": "Some engines bury the rear plugs under the intake, and some aluminum heads strip easily if over-tightened. "
                "Look up your engine first. Use the Repair videos button for your exact vehicle.",
    },
    {
        "title": "Find a bad ignition coil",
        "family": None,
        "applies": "A misfire on one cylinder, like P0301 to P0308, on engines with a coil on each plug",
        "needs": "A socket or wrench for the coil bolt, and this app to read and clear codes",
        "steps": [
            "Note which cylinder the code names.",
            "With the engine off, swap that cylinder's coil with the one next to it.",
            "Clear the code and drive normally until the check-engine light returns or the code comes back.",
            "If the misfire moved to the other cylinder, that coil is bad. If it stayed, check the plug next.",
        ],
        "note": "A flashing check-engine light means a severe misfire. Avoid hard driving, since it can damage the "
                "catalytic converter.",
    },
    {
        "title": "Fix a loose or bad gas cap",
        "family": None,
        "applies": "EVAP leak codes like P0455 and P0457, or a check-engine light right after getting gas",
        "needs": "Possibly a new gas cap made for your vehicle",
        "steps": [
            "Take the cap off and look at the rubber seal. Replace the cap if it's cracked, flattened or missing.",
            "Put it back on and tighten it until it clicks.",
            "Drive normally for a few days. The light may go out by itself once the vehicle re-tests.",
            "If the code returns with a good cap, the leak is likely in the EVAP hoses or a valve, so have it smoke-tested.",
        ],
        "note": "",
    },
    {
        "title": "Replace an oxygen (O2) sensor",
        "family": None,
        "applies": "O2 sensor codes, once wiring and exhaust leaks have been ruled out",
        "needs": "The right sensor, an oxygen sensor socket, a ratchet, and penetrating oil",
        "steps": [
            "Use the code to find which one it is. Bank 1 is the side with cylinder 1, and sensor 1 is before the catalytic "
            "converter.",
            "Let the exhaust cool until it's safe to touch. If you have to go under the vehicle, use jack stands.",
            "Unplug the sensor, and spray the threads with penetrating oil if it's rusty.",
            "Unscrew it with the sensor socket.",
            "Thread the new sensor in by hand, tighten it to spec, and plug it in, keeping the wire away from hot parts.",
        ],
        "note": "Many codes that name an O2 sensor are really caused by a vacuum or exhaust leak. Check for those first.",
    },
    {
        "title": "Engine is overheating",
        "family": None,
        "applies": "Temperature gauge high, coolant smell, steam, or code P0217",
        "needs": "The right coolant for your vehicle",
        "steps": [
            "Pull over safely and turn the engine off. Driving while overheated can ruin the engine.",
            "Never open the radiator or coolant cap while it's hot. Wait until the engine is fully cool.",
            "Check the coolant level when cold, and top it up with the right coolant if it's low.",
            "Look for leaks at the hoses, the radiator and under the vehicle.",
            "With the engine running, make sure the cooling fan comes on as it warms up.",
            "If it keeps overheating, the likely causes are the thermostat, water pump, fan or a head gasket. Have it "
            "checked before driving far.",
        ],
        "note": "",
    },
    {
        "title": "Replace brake pads",
        "family": None,
        "applies": "Squealing or grinding brakes, or pads worn thin on disc brakes",
        "needs": "New pads, a jack and jack stands, a lug wrench, a socket set, a C-clamp and a torque wrench",
        "steps": [
            "Park on level ground, loosen the lug nuts, lift the vehicle and support it on jack stands.",
            "Remove the wheel, then the caliper bolts. Hang the caliper with wire, not by its brake hose.",
            "Note how the old pads sit, then take them out and check the rotor for deep grooves.",
            "Slowly press the caliper piston back with the C-clamp, watching that the brake fluid doesn't overflow.",
            "Fit the new pads and hardware, refit the caliper, and tighten everything to spec.",
            "Before moving the vehicle, pump the brake pedal until it's firm. Repeat on the other side of the same axle.",
        ],
        "note": "Brakes are safety-critical. Some rear calipers screw in instead of pressing in, and electronic parking "
                "brakes need a special procedure. Look up your exact vehicle, and go to a shop if you're not sure.",
    },
]


def search(words):
    """Guides whose title or description mention every word (not the steps: they mention too much in passing)."""
    return [g for g in GUIDES if mentions(g["title"] + " " + g["applies"], words)]


# --- Normal ranges for live data (the iPhone app's copy is generated from this) -----------------
# (words in the reading's name, what to show, flag below, flag above). First match wins; no text = show nothing.
# Compared in the units the app shows: °F, %, V. These are typical values, so most only inform and never flag.
NORMAL_RANGES = [
    ("absolute", None, None, None), ("relative", None, None, None), ("commanded", None, None, None),
    ("fuel trim", "Normal: -10 to +10 %", -10, 10),
    ("coolant", "Warmed up: 180 to 220 °F", None, 235),
    ("oil temp", "Warmed up: 190 to 250 °F", None, 270),
    ("transmission", "Warmed up: 150 to 200 °F", None, 240),
    ("intake air", "Usually near the outside temperature", None, None),
    ("rpm", "Idle: about 600 to 1,000 rpm", None, None),
    ("engine speed", "Idle: about 600 to 1,000 rpm", None, None),
    ("engine load", "Idle: about 15 to 35 %", None, None),
    ("throttle position", "Idle: usually under 20 %", None, None),
    ("mass air", "Idle: about 2 to 7 g/s, more on big engines", None, None),
    ("intake manifold", "Idle: about 20 to 40 kPa", None, None),
    ("barometric", "About 100 kPa near sea level", None, None),
    ("o2 sensor", "Front sensor swings about 0.1 to 0.9 V", None, None),
    ("voltage", "Engine running: 13.5 to 14.8 V", None, 15.5),
    ("ignition timing", "Idle: usually 5 to 20°", None, None),
]
NORMAL_NOTE = "Normal ranges are typical values and vary by vehicle. Check the service manual to be sure."


def normal_range(name):
    """-> (text, flag below, flag above) for a live reading, or None."""
    low = name.lower()
    for key, text, below, above in NORMAL_RANGES:
        if key in low:
            return (text, below, above) if text else None
    return None


def outside_normal(name, value):
    r = normal_range(name)
    return bool(r) and ((r[1] is not None and value < r[1]) or (r[2] is not None and value > r[2]))


# --- Step-by-step help: each answer leads to the next check (the iPhone app's copy is generated from this) ---
def _opts(*pairs):
    return list(pairs)


GUIDED = {
    "misfire": {
        "title": "Find a misfire",
        "codes": ["P0300"] + ["P03%02d" % n for n in range(1, 13)],
        "start": "flash",
        "nodes": {
            "flash": {"text": "Is the check-engine light flashing, or is the engine shaking badly?",
                      "options": _opts(("Yes", "severe"), ("No", "which"))},
            "severe": {"text": "A flashing light means unburned fuel can overheat and ruin the catalytic converter. "
                               "Drive gently and as little as possible until this is fixed.",
                       "options": _opts(("Okay, keep going", "which"),)},
            "which": {"text": "What does the code say? P0301 to P0312 name one cylinder. P0300 means random or several.",
                      "options": _opts(("One cylinder", "coil"), ("P0300, random or several", "multi"))},
            "coil": {"text": "With the engine off and cool, swap that cylinder's ignition coil with a neighbor's. "
                             "Clear the codes and drive. Did the misfire move to the other cylinder?",
                     "options": _opts(("Yes, it moved", "badcoil"), ("No, it stayed", "plug"),
                                      ("This engine has no separate coils", "plug"))},
            "badcoil": {"text": "The coil you moved is bad. Replace it, then clear the codes and drive to confirm.",
                        "options": []},
            "plug": {"text": "Pull that cylinder's spark plug. Is it worn, cracked, oily or wet?",
                     "options": _opts(("Worn or cracked", "newplug"), ("Oily or wet", "wetplug"), ("It looks fine", "swapplug"))},
            "newplug": {"text": "Replace the spark plugs. If one is worn, the others usually are too.", "options": []},
            "wetplug": {"text": "Something is getting into that cylinder. Oil can mean a leaking valve cover or tube seal. "
                                "Coolant can mean a head gasket problem, so have that checked before driving much.",
                        "options": []},
            "swapplug": {"text": "Swap that spark plug with a neighbor's, clear the codes and drive. Did the misfire move?",
                         "options": _opts(("Yes, it moved", "newplug"), ("No, it stayed", "deeper"))},
            "deeper": {"text": "The coil and plug are fine, so the fuel injector and compression are next. A shop can "
                               "test both quickly. Compare before buying parts.", "options": []},
            "multi": {"text": "With the engine warmed up and idling, look at long-term fuel trim in Live data. "
                              "Is it above +10 %?",
                      "options": _opts(("Yes, above +10 %", "multilean"), ("No", "multiage"), ("I can't read it", "multiage"))},
            "multilean": {"text": "The engine is running lean, which can cause random misfires. Look for vacuum leaks "
                                  "first. The lean guide has the next steps.", "options": []},
            "multiage": {"text": "When were the spark plugs last changed?",
                         "options": _opts(("Over 60,000 miles ago, or not sure", "newplug"), ("Recently", "multideep"))},
            "multideep": {"text": "With fresh plugs and normal fuel trims, the next checks are fuel pressure, a shared "
                                  "coil pack if it has one, and compression. A shop can test these.", "options": []},
        },
    },
    "lean": {
        "title": "Find why it's running lean",
        "codes": ["P0171", "P0174"],
        "start": "trim",
        "nodes": {
            "trim": {"text": "Warm up the engine, park with the brake on, and watch long-term fuel trim in Live data at "
                             "idle and then holding 2,500 rpm. What do you see?",
                     "options": _opts(("High at idle, better at 2,500 rpm", "vac"), ("High at both", "fuel"),
                                      ("Normal at both", "intermittent"))},
            "vac": {"text": "That points to a vacuum leak. With the engine off, check the hoses and the rubber intake "
                            "boot after the air flow sensor for cracks or loose clamps. Find anything?",
                    "options": _opts(("Yes", "fixvac"), ("No", "smoke"))},
            "fixvac": {"text": "Fix the leak, clear the codes and drive. Fuel trim should come back within about 10 %.",
                       "options": []},
            "smoke": {"text": "Small leaks are hard to see. A shop can find them quickly with a smoke test.", "options": []},
            "fuel": {"text": "Clean the mass air flow sensor with MAF cleaner only, let it dry, clear the codes and drive. "
                             "Did fuel trim improve?",
                     "options": _opts(("Yes", "fixedmaf"), ("No", "pressure"))},
            "fixedmaf": {"text": "A dirty sensor was likely the cause. Check that the air filter is clean too.", "options": []},
            "pressure": {"text": "Next, check fuel pressure against the spec for your vehicle. A weak pump or clogged "
                                 "filter can do this. An exhaust leak ahead of the oxygen sensor can too.", "options": []},
            "intermittent": {"text": "It may only happen sometimes. Check the air filter and intake ducts, clear the "
                                     "codes, and see if it comes back.", "options": []},
        },
    },
    "evap": {
        "title": "Find an EVAP leak",
        "codes": ["P0440", "P0442", "P0455", "P0456", "P0457"],
        "start": "cap",
        "nodes": {
            "cap": {"text": "Check the gas cap first. Is it loose, or is its rubber seal cracked or worn?",
                    "options": _opts(("Yes", "fixcap"), ("It looks fine", "again"))},
            "fixcap": {"text": "Tighten it until it clicks, or replace it if the seal is bad. Clear the codes. It can "
                               "take several drives for the car to re-check. Did the code come back?",
                       "options": _opts(("Yes", "hoses"), ("No", "done"))},
            "done": {"text": "That was it. No more steps needed.", "options": []},
            "again": {"text": "Tighten it anyway until it clicks, clear the codes and drive for a few days. Did the code "
                              "come back?", "options": _opts(("Yes", "hoses"), ("No", "done"))},
            "hoses": {"text": "Look at the rubber EVAP hoses you can reach, especially near the engine and the charcoal "
                              "canister. Find a crack or a loose one?",
                      "options": _opts(("Yes", "fixhose"), ("No", "smoke"))},
            "fixhose": {"text": "Replace that hose, clear the codes and drive for a few days to confirm.", "options": []},
            "smoke": {"text": "A shop can find the leak with a smoke test. The purge and vent valves are also common causes.",
                      "options": []},
        },
    },
    "catalyst": {
        "title": "Check the catalytic converter",
        "codes": ["P0420", "P0430"],
        "start": "others",
        "nodes": {
            "others": {"text": "Are there other codes too, like misfires, lean or rich codes, or oxygen sensor codes?",
                       "options": _opts(("Yes", "fixfirst"), ("No", "leak"))},
            "fixfirst": {"text": "Fix those first. They can set this code, and they can ruin a new converter. Then clear "
                                 "the codes and see if this one returns.", "options": []},
            "leak": {"text": "Check for an exhaust leak ahead of the rear oxygen sensor: ticking when cold, or black soot "
                             "at a joint. Find one?",
                     "options": _opts(("Yes", "fixleak"), ("No", "sensor"))},
            "fixleak": {"text": "Fix the leak, clear the codes and drive. A leak can make the rear sensor read wrong.",
                        "options": []},
            "sensor": {"text": "With the engine warmed up, hold 2,500 rpm in park and watch the rear oxygen sensor voltage "
                               "in Live data, if your vehicle shows it. What is it doing?",
                       "options": _opts(("Fairly steady", "ok"), ("Swinging up and down quickly", "worn"),
                                        ("I can't see it", "shop"))},
            "ok": {"text": "The converter may be okay. Clear the code and see if it returns. If it does, have the sensor "
                           "and converter tested.", "options": []},
            "worn": {"text": "The converter is likely worn out. Have a shop confirm before buying one, because they're "
                             "expensive. Check your warranty: US federal emissions coverage is often 8 years or 80,000 miles.",
                     "options": []},
            "shop": {"text": "A shop can test the converter before you buy one. Converters are expensive, so it's worth confirming.",
                     "options": []},
        },
    },
    "cold": {
        "title": "Engine not warming up",
        "codes": ["P0128"],
        "start": "level",
        "nodes": {
            "level": {"text": "With the engine fully cold, check the coolant level in the overflow tank. Is it between the marks?",
                      "options": _opts(("Yes", "drive"), ("It's low", "low"))},
            "low": {"text": "Top it up with the coolant type your manual lists, and look for leaks. Then clear the code "
                            "and see if it returns.", "options": []},
            "drive": {"text": "Drive for about 15 minutes and watch coolant temperature in Live data. Where does it end up?",
                      "options": _opts(("Stays under about 180 °F", "stat"), ("Reaches 190 °F or more", "sensor"))},
            "stat": {"text": "The thermostat is probably stuck open. Replacing it is the usual fix.", "options": []},
            "sensor": {"text": "The engine is warming up fine. Check the coolant temperature sensor and its connector, "
                               "then clear the code and see if it returns.", "options": []},
        },
    },
    "overheat": {
        "title": "Engine overheating",
        "codes": ["P0217"],
        "start": "safe",
        "nodes": {
            "safe": {"text": "Pull over and turn the engine off if the gauge is in the red. Never open the radiator cap "
                             "while it's hot, because the coolant can spray out and burn you. Is the engine fully cool?",
                     "options": _opts(("Yes, it's cool", "level"), ("Not yet", "wait"))},
            "wait": {"text": "Wait at least 30 minutes, then come back to this step.", "options": _opts(("It's cool now", "level"),)},
            "level": {"text": "Check the coolant level in the overflow tank. Is it low?",
                      "options": _opts(("Yes, it's low", "leak"), ("No, it's fine", "fan"))},
            "leak": {"text": "Top it up with the right coolant and look for leaks under the car and around the hoses. Coolant "
                             "that keeps dropping with no visible leak needs a shop to check the head gasket.", "options": []},
            "fan": {"text": "Start the engine and turn the A/C on. Keep your hands clear of the fan. Do the radiator fans run?",
                    "options": _opts(("Yes", "stat"), ("No", "badfan"))},
            "badfan": {"text": "Check the fan's fuse and relay, then the fan itself. A shop can test the fan circuit.", "options": []},
            "stat": {"text": "The next suspects are a stuck thermostat, a clogged radiator, or a weak water pump. Have them "
                           "checked before driving far, because overheating can badly damage an engine.", "options": []},
        },
    },
    "charging": {
        "title": "Check the charging system",
        "codes": ["P0562", "P0563"],
        "start": "volts",
        "nodes": {
            "volts": {"text": "With the engine running, read the battery voltage in Live data or with a meter. What is it?",
                      "options": _opts(("13.5 to 14.8 V", "okay"), ("Under 13 V", "low"), ("Over 15 V", "high"))},
            "okay": {"text": "Charging looks normal right now. Clean and tighten the battery terminals, then test the "
                             "battery itself. Clear the code and see if it returns.", "options": []},
            "low": {"text": "With the engine off, check the belt and the battery terminals. Is the belt loose or cracked, or "
                            "are the terminals corroded?",
                    "options": _opts(("Yes", "fixbelt"), ("No, they look fine", "alt"))},
            "fixbelt": {"text": "Fix that first, then read the voltage again with the engine running.", "options": []},
            "alt": {"text": "The alternator is likely weak. Most parts stores can test it for free before you buy one.",
                    "options": []},
            "high": {"text": "The alternator is probably overcharging, which can damage the battery and electronics. Have "
                             "it checked soon.", "options": []},
        },
    },
}


def guided_topic(code):
    """The step-by-step help for a code, as a key of GUIDED, or None."""
    base = code.split("-")[0].upper()
    return next((k for k, t in GUIDED.items() if base in t["codes"]), None)
