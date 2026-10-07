"""
Relearns, resets and bleeding: procedures you can do by hand, with no scan-tool commands.

Each guide: title, family ("ford", "gm" or None for most vehicles), applies (which vehicles),
needs (tools), steps, and an optional note (when a shop or scan tool is needed instead).
"""

GUIDES = [
    {
        "title": "Add a key (Ford anti-theft, PATS)",
        "family": "ford",
        "applies": "Most Ford, Lincoln and Mercury vehicles with chip keys, when you already have two working keys",
        "needs": "Two keys that already start the vehicle, and the new chip key cut to fit",
        "steps": [
            "Put working key 1 in and turn it to ON for about 3 seconds. Turn it OFF and take it out.",
            "Within 10 seconds, put working key 2 in and turn it to ON for about 3 seconds. Turn it OFF and "
            "take it out.",
            "Within 20 seconds, put the new key in and turn it to ON for about 3 seconds.",
            "If the theft light on the dash comes on for about 3 seconds and goes out, the new key is "
            "programmed. Start the engine to check.",
        ],
        "note": "With only one working key, a locksmith or dealer has to program it.",
    },
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
        "title": "Anti-theft relearn (GM Passlock)",
        "family": "gm",
        "applies": "Many GM cars and trucks from about 1996-2007 (including 1999-2007 Silverado and Sierra) when "
                   "the engine cranks but won't start and the security light is on or flashing",
        "needs": "A charged battery (connect a charger if you have one)",
        "steps": [
            "Turn the key to ON (don't crank). The security light should come on or flash.",
            "Leave it for about 10 minutes, until the security light goes off or stops flashing.",
            "Turn the key OFF for 5 seconds.",
            "Start the engine. If it still won't start, repeat steps 1-3 two more times (30 minutes total), "
            "then try again.",
        ],
        "note": "If it keeps coming back, the sensor in the ignition lock cylinder is often worn out.",
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
]


def for_family(fam):
    """Guides for this make's family first, then the ones for most vehicles; other makes' guides left out."""
    mine = [g for g in GUIDES if fam and g["family"] == fam]
    general = [g for g in GUIDES if g["family"] is None]
    if not fam:
        return general + [g for g in GUIDES if g["family"]]
    return mine + general
