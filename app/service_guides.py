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
