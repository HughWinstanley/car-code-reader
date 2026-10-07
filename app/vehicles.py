"""
Makes and models for the vehicle picker (US market, OBD-II era: 1996 and newer).

Body types: t = pickup truck, s = SUV, c = car, v = van.
Family tells the scanner which module map to use for ABS / airbag:
  "Ford" (Ford, Lincoln, Mercury), "GM" (Chevrolet, GMC, Buick, Cadillac, ...), else the make itself.
Fully electric models are left out: they have no engine codes for an OBD-II reader to read.
"""

import datetime

FIRST_YEAR = 1996


OBD1_FIRST_YEAR = 1981


def years(make=None):
    """Newest first. Makes with a blink-code guide also go back to 1981 (OBD-I)."""
    first = FIRST_YEAR
    if make:
        import obd1
        if obd1.group_for(family_of(make)):
            first = OBD1_FIRST_YEAR
    return list(range(datetime.date.today().year + 1, first - 1, -1))


def _m(text):
    """'F-150:t, Ranger:t' -> [('F-150', 't'), ('Ranger', 't')]"""
    out = []
    for part in text.split(","):
        part = part.strip()
        if part:
            name, _, kind = part.rpartition(":")
            out.append((name.strip(), kind.strip()))
    return out


# make: (badge letters, family, models)
MAKES = {
    "Ford": ("FD", "Ford", _m(
        "F-150:t, F-250 Super Duty:t, F-350 Super Duty:t, F-450 Super Duty:t, F-250 (1996-1999):t, Ranger:t, "
        "Maverick:t, Explorer:s, Explorer Sport Trac:t, Expedition:s, Excursion:s, Bronco:s, Bronco Sport:s, "
        "Escape:s, Edge:s, Flex:s, EcoSport:s, Freestyle:s, Mustang:c, Taurus:c, Fusion:c, Focus:c, Fiesta:c, "
        "Escort:c, Contour:c, Crown Victoria:c, Five Hundred:c, Thunderbird:c, Probe:c, Aspire:c, C-Max:c, GT:c, "
        "Windstar:v, Freestar:v, E-Series / Econoline:v, Transit:v, Transit Connect:v")),
    "Chevrolet": ("CHV", "GM", _m(
        "Silverado 1500:t, Silverado 2500HD:t, Silverado 3500HD:t, C/K 1500:t, C/K 2500:t, C/K 3500:t, S-10:t, "
        "Colorado:t, Avalanche:t, SSR:t, Tahoe:s, Suburban:s, Blazer:s, TrailBlazer:s, Equinox:s, Traverse:s, "
        "Trax:s, Tracker:s, HHR:s, Captiva Sport:s, Malibu:c, Impala:c, Monte Carlo:c, Cavalier:c, Cobalt:c, "
        "Cruze:c, Sonic:c, Aveo:c, Spark:c, Camaro:c, Corvette:c, Lumina:c, Prizm:c, Metro:c, Volt:c, "
        "Caprice:c, Venture:v, Uplander:v, Astro:v, Express:v, City Express:v")),
    "GMC": ("GMC", "GM", _m(
        "Sierra 1500:t, Sierra 2500HD:t, Sierra 3500HD:t, Sierra C/K:t, Sonoma:t, Canyon:t, Yukon:s, "
        "Yukon XL:s, Jimmy:s, Envoy:s, Acadia:s, Terrain:s, Safari:v, Savana:v")),
    "Buick": ("BU", "GM", _m(
        "LeSabre:c, Century:c, Regal:c, Park Avenue:c, LaCrosse:c, Lucerne:c, Allure:c, Verano:c, Cascada:c, "
        "Rendezvous:s, Rainier:s, Enclave:s, Encore:s, Envision:s, Terraza:v")),
    "Cadillac": ("CA", "GM", _m(
        "DeVille:c, DTS:c, Seville:c, STS:c, CTS:c, ATS:c, XTS:c, CT4:c, CT5:c, CT6:c, Eldorado:c, Catera:c, "
        "XLR:c, ELR:c, Escalade:s, Escalade ESV:s, Escalade EXT:t, SRX:s, XT4:s, XT5:s, XT6:s")),
    "Pontiac": ("PO", "GM", _m(
        "Grand Prix:c, Grand Am:c, Bonneville:c, Firebird:c, Sunfire:c, G6:c, G8:c, G5:c, Vibe:c, Solstice:c, "
        "GTO:c, Aztek:s, Torrent:s, Montana:v, Trans Sport:v")),
    "Oldsmobile": ("OL", "GM", _m(
        "Alero:c, Intrigue:c, Aurora:c, Cutlass:c, Eighty-Eight:c, Achieva:c, Bravada:s, Silhouette:v")),
    "Saturn": ("ST", "GM", _m(
        "S-Series:c, L-Series:c, Ion:c, Aura:c, Sky:c, Astra:c, Vue:s, Outlook:s, Relay:v")),
    "Hummer": ("HM", "GM", _m("H1:s, H2:s, H3:s, H3T:t")),
    "Lincoln": ("LN", "Ford", _m(
        "Town Car:c, Continental:c, LS:c, MKZ:c, Zephyr:c, MKS:c, Mark VIII:c, Navigator:s, Aviator:s, "
        "MKX:s, Nautilus:s, MKC:s, Corsair:s, MKT:s, Blackwood:t, Mark LT:t")),
    "Mercury": ("MC", "Ford", _m(
        "Grand Marquis:c, Sable:c, Milan:c, Montego:c, Cougar:c, Mystique:c, Tracer:c, Marauder:c, "
        "Mountaineer:s, Mariner:s, Villager:v, Monterey:v")),
    "Dodge": ("DG", "Dodge", _m(
        "Ram 1500 (to 2010):t, Ram 2500 (to 2010):t, Ram 3500 (to 2010):t, Dakota:t, Durango:s, Nitro:s, "
        "Journey:s, Caliber:c, Charger:c, Challenger:c, Dart:c, Neon:c, Stratus:c, Intrepid:c, Avenger:c, "
        "Magnum:c, Viper:c, Caravan:v, Grand Caravan:v, Ram Van:v, Sprinter:v")),
    "Ram": ("RAM", "Ram", _m("1500:t, 2500:t, 3500:t, ProMaster:v, ProMaster City:v")),
    "Jeep": ("JP", "Jeep", _m(
        "Wrangler:s, Grand Cherokee:s, Cherokee:s, Liberty:s, Compass:s, Patriot:s, Commander:s, Renegade:s, "
        "Wagoneer:s, Grand Wagoneer:s, Gladiator:t")),
    "Chrysler": ("CHR", "Chrysler", _m(
        "300:c, 300M:c, Concorde:c, Sebring:c, 200:c, Cirrus:c, LHS:c, PT Cruiser:c, Crossfire:c, "
        "Pacifica:v, Town & Country:v, Voyager:v, Aspen:s")),
    "Plymouth": ("PL", "Plymouth", _m("Neon:c, Breeze:c, Prowler:c, Voyager:v, Grand Voyager:v")),
    "Toyota": ("TY", "Toyota", _m(
        "Tacoma:t, Tundra:t, T100:t, 4Runner:s, Sequoia:s, Land Cruiser:s, Highlander:s, RAV4:s, FJ Cruiser:s, "
        "Venza:s, C-HR:s, Corolla Cross:s, Camry:c, Corolla:c, Avalon:c, Prius:c, Yaris:c, Echo:c, Celica:c, "
        "Supra:c, Matrix:c, Solara:c, 86:c, Sienna:v")),
    "Lexus": ("LX", "Toyota", _m(
        "ES:c, IS:c, GS:c, LS:c, RC:c, SC:c, CT:c, HS:c, RX:s, GX:s, LX:s, NX:s, UX:s")),
    "Scion": ("SC", "Toyota", _m("tC:c, xB:c, xA:c, xD:c, iQ:c, FR-S:c, iA:c, iM:c")),
    "Honda": ("HO", "Honda", _m(
        "Accord:c, Civic:c, Fit:c, Insight:c, Prelude:c, S2000:c, Clarity:c, CR-V:s, HR-V:s, Pilot:s, "
        "Passport:s, Element:s, Ridgeline:t, Odyssey:v")),
    "Acura": ("AC", "Honda", _m(
        "Integra:c, TL:c, TSX:c, RL:c, RLX:c, ILX:c, TLX:c, CL:c, RSX:c, NSX:c, MDX:s, RDX:s, ZDX:s, SLX:s")),
    "Nissan": ("NI", "Nissan", _m(
        "Altima:c, Maxima:c, Sentra:c, Versa:c, 350Z:c, 370Z:c, 200SX:c, Cube:c, GT-R:c, Frontier:t, Titan:t, "
        "Pathfinder:s, Xterra:s, Armada:s, Murano:s, Rogue:s, Juke:s, Kicks:s, Quest:v, NV200:v, NV:v")),
    "Infiniti": ("IN", "Nissan", _m(
        "G35:c, G37:c, I30:c, I35:c, M35:c, M45:c, Q40:c, Q50:c, Q60:c, Q70:c, QX4:s, QX50:s, QX56:s, QX60:s, "
        "QX70:s, QX80:s, FX35:s, FX45:s, EX35:s, JX35:s")),
    "Hyundai": ("HY", "Hyundai", _m(
        "Elantra:c, Sonata:c, Accent:c, Azera:c, Genesis:c, Veloster:c, Tiburon:c, Ioniq Hybrid:c, Santa Fe:s, "
        "Tucson:s, Palisade:s, Kona:s, Venue:s, Veracruz:s, Santa Cruz:t, Entourage:v")),
    "Genesis": ("GN", "Hyundai", _m("G70:c, G80:c, G90:c, GV70:s, GV80:s")),
    "Kia": ("KIA", "Kia", _m(
        "Optima:c, K5:c, Forte:c, Rio:c, Soul:c, Stinger:c, Cadenza:c, Spectra:c, Sephia:c, Sportage:s, "
        "Sorento:s, Telluride:s, Seltos:s, Niro:s, Borrego:s, Sedona:v, Carnival:v")),
    "Mazda": ("MZ", "Mazda", _m(
        "Mazda3:c, Mazda6:c, 626:c, Protege:c, Millenia:c, MX-5 Miata:c, RX-8:c, Mazda2:c, CX-3:s, CX-30:s, "
        "CX-5:s, CX-7:s, CX-9:s, Tribute:s, B-Series:t, MPV:v, Mazda5:v")),
    "Subaru": ("SU", "Subaru", _m(
        "Impreza:c, Legacy:c, WRX:c, BRZ:c, Outback:s, Forester:s, Crosstrek:s, Ascent:s, Tribeca:s, Baja:t")),
    "Mitsubishi": ("MI", "Mitsubishi", _m(
        "Lancer:c, Galant:c, Eclipse:c, Mirage:c, Diamante:c, 3000GT:c, Outlander:s, Outlander Sport:s, "
        "Eclipse Cross:s, Montero:s, Montero Sport:s, Endeavor:s, Raider:t")),
    "Suzuki": ("SZ", "Suzuki", _m(
        "Esteem:c, Aerio:c, Forenza:c, Reno:c, SX4:c, Kizashi:c, Swift:c, Vitara:s, Grand Vitara:s, "
        "XL-7:s, Sidekick:s, Equator:t")),
    "Isuzu": ("IS", "GM", _m("Rodeo:s, Trooper:s, Axiom:s, Ascender:s, Amigo:s, Hombre:t, i-Series:t")),
    "Volkswagen": ("VW", "Volkswagen", _m(
        "Jetta:c, Golf:c, GTI:c, Passat:c, Beetle:c, CC:c, Arteon:c, Cabrio:c, Eos:c, Rabbit:c, Phaeton:c, "
        "Tiguan:s, Touareg:s, Atlas:s, Taos:s, Routan:v, EuroVan:v")),
    "Audi": ("AU", "Volkswagen", _m("A3:c, A4:c, A5:c, A6:c, A7:c, A8:c, TT:c, R8:c, Q3:s, Q5:s, Q7:s, Q8:s, allroad:s")),
    "BMW": ("BMW", "BMW", _m(
        "3 Series:c, 5 Series:c, 7 Series:c, 1 Series:c, 2 Series:c, 4 Series:c, 6 Series:c, 8 Series:c, Z3:c, "
        "Z4:c, X1:s, X2:s, X3:s, X4:s, X5:s, X6:s, X7:s")),
    "Mini": ("MN", "BMW", _m("Cooper:c, Clubman:c, Countryman:s, Paceman:c")),
    "Mercedes-Benz": ("MB", "Mercedes-Benz", _m(
        "C-Class:c, E-Class:c, S-Class:c, CLA:c, CLK:c, CLS:c, SL:c, SLK:c, ML / GLE:s, GL / GLS:s, GLK / GLC:s, "
        "GLA:s, G-Class:s, Sprinter:v, Metris:v")),
    "Volvo": ("VO", "Volvo", _m("S40:c, S60:c, S70:c, S80:c, S90:c, V40:c, V50:c, V60:c, V70:c, C30:c, C70:c, "
                                "XC40:s, XC60:s, XC70:s, XC90:s")),
    "Saab": ("SA", "GM", _m("9-3:c, 9-5:c, 9-2X:c, 9-7X:s")),
    "Porsche": ("PR", "Volkswagen", _m("911:c, Boxster:c, Cayman:c, Panamera:c, Cayenne:s, Macan:s")),
    "Jaguar": ("JA", "Jaguar", _m("XJ:c, XK:c, XF:c, XE:c, S-Type:c, X-Type:c, F-Type:c, F-Pace:s, E-Pace:s")),
    "Land Rover": ("LR", "Land Rover", _m(
        "Range Rover:s, Range Rover Sport:s, Range Rover Evoque:s, Range Rover Velar:s, Discovery:s, "
        "Discovery Sport:s, LR2:s, LR3:s, LR4:s, Freelander:s, Defender:s")),
    "Fiat": ("FI", "Chrysler", _m("500:c, 500X:s, 500L:c, 124 Spider:c")),
}

FULL_SUPPORT_FAMILIES = ("Ford", "GM")


def support_text(make):
    family = MAKES[make][1]
    if family in FULL_SUPPORT_FAMILIES:
        return "Engine, ABS and airbag"
    return "Engine codes, some ABS and airbag"


def family_of(make):
    return MAKES.get(make, ("", make, []))[1]
