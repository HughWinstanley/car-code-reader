"""
Makes and models for the vehicle picker (US market).

Each model is "Name:type:years" where type is t (pickup), s (SUV), c (car) or v (van), and years are
US model years: "1996-2004", an open range "1999-" (still made), or several ranges "1983-2001|2014-2023".
The picker only offers years inside these ranges, and never earlier than the oldest year the app can
read for that make: 1981 for makes with a blink-code guide (OBD-I), otherwise 1996 (OBD-II).
Years are padded by one at each end of a range so a car sold early or late as the next/previous model
year isn't cut off.

Family tells the scanner which module map to use for ABS / airbag:
  "Ford" (Ford, Lincoln, Mercury), "GM" (Chevrolet, GMC, Buick, Cadillac, ...), else the make itself.
Fully electric models are left out: they have no engine codes for an OBD-II reader to read.
"""

import datetime

FIRST_YEAR = 1996
OBD1_FIRST_YEAR = 1981
PAD = 1


def _this_year():
    return datetime.date.today().year


def _ranges(spec):
    out = []
    for part in (spec or "1981-").split("|"):
        if "-" not in part:  # a single model year, e.g. "2006"
            out.append((int(part) - PAD, int(part) + PAD))
            continue
        a, _, b = part.partition("-")
        start = int(a)
        end = int(b) if b else _this_year() + 1
        out.append((start - PAD, end + (PAD if b else 0)))
    return out


def _m(text):
    """'F-150:t:1981-, Tempo:c:1984-1994' -> [('F-150', 't', '1981-'), ...]"""
    out = []
    for part in text.split(","):
        part = part.strip()
        if part:
            name, kind, yrs = (part.rsplit(":", 2) + ["", ""])[:3]
            out.append((name.strip(), kind.strip(), yrs.strip()))
    return out


# make: (badge letters, family, models)
MAKES = {
    "Ford": ("FD", "Ford", _m(
        "F-150:t:1981-, F-250 Super Duty:t:1999-, F-350 Super Duty:t:1999-, F-450 Super Duty:t:2008-, "
        "F-250 / F-350 (before Super Duty):t:1981-1999, Ranger:t:1983-2011|2019-, Maverick:t:2022-, "
        "Explorer:s:1991-, Explorer Sport Trac:t:2001-2010, Expedition:s:1997-, Excursion:s:2000-2005, "
        "Bronco:s:1981-1996|2021-, Bronco II:s:1984-1990, Bronco Sport:s:2021-, Escape:s:2001-, "
        "Edge:s:2007-2024, Flex:s:2009-2019, EcoSport:s:2018-2022, Freestyle:s:2005-2007, Mustang:c:1981-, "
        "Taurus:c:1986-2007|2010-2019, Fusion:c:2006-2020, Focus:c:2000-2018, Fiesta:c:2011-2019, "
        "Escort:c:1981-2003, Tempo:c:1984-1994, Festiva:c:1988-1993, Contour:c:1995-2000, "
        "Crown Victoria:c:1983-2011, Five Hundred:c:2005-2007, Thunderbird:c:1981-1997|2002-2005, "
        "Probe:c:1989-1997, Aspire:c:1994-1997, C-Max:c:2013-2018, GT:c:2005-2006|2017-2022, "
        "Aerostar:v:1986-1997, Windstar:v:1995-2003, Freestar:v:2004-2007, E-Series / Econoline:v:1981-, "
        "Transit:v:2015-, Transit Connect:v:2010-2023")),
    "Chevrolet": ("CHV", "GM", _m(
        "Silverado 1500:t:1999-, Silverado 2500 / 2500HD:t:1999-, Silverado 3500 / 3500HD:t:2001-, "
        "C/K 1500:t:1981-1999, C/K 2500:t:1981-2000, C/K 3500:t:1981-2000, S-10:t:1982-2004, "
        "Colorado:t:2004-2012|2015-, Avalanche:t:2002-2013, SSR:t:2003-2006, Tahoe:s:1995-, "
        "Suburban:s:1981-, Blazer (full-size K5):s:1981-1994, Blazer (S-10 Blazer):s:1983-2005, Blazer:s:2019-, "
        "TrailBlazer:s:2002-2009|2021-, Equinox:s:2005-, Traverse:s:2009-, Trax:s:2015-, Tracker:s:1989-2004, "
        "HHR:s:2006-2011, Captiva Sport:s:2012-2015, Malibu:c:1981-1983|1997-2025, "
        "Impala:c:1981-1985|1994-1996|2000-2020, Monte Carlo:c:1981-1988|1995-2007, Cavalier:c:1982-2005, "
        "Cobalt:c:2005-2010, Cruze:c:2011-2019, Sonic:c:2012-2020, Aveo:c:2004-2011, Spark:c:2013-2022, "
        "Camaro:c:1981-2002|2010-2024, Corvette:c:1981-1982|1984-, Lumina:c:1990-2001, Celebrity:c:1982-1990, "
        "Beretta:c:1987-1996, Corsica:c:1987-1996, Citation:c:1981-1985, Chevette:c:1981-1987, "
        "Prizm:c:1990-2002, Metro:c:1989-2001, Volt:c:2011-2019, Caprice:c:1981-1996, Lumina APV:v:1990-1996, "
        "Venture:v:1997-2005, Uplander:v:2005-2009, Astro:v:1985-2005, Chevy Van / G-Series:v:1981-1996, "
        "Express:v:1996-, City Express:v:2015-2018")),
    "GMC": ("GMC", "GM", _m(
        "Sierra 1500:t:1999-, Sierra 2500 / 2500HD:t:1999-, Sierra 3500 / 3500HD:t:2001-, "
        "Sierra C/K 1500 / 2500 / 3500:t:1981-2000, S-15:t:1982-1990, Sonoma:t:1991-2004, "
        "Canyon:t:2004-2012|2015-, Yukon:s:1992-, Yukon XL:s:2000-, Suburban (GMC):s:1981-1999, "
        "Jimmy:s:1981-2005, Envoy:s:1998-2000|2002-2009, Acadia:s:2007-, Terrain:s:2010-, Safari:v:1985-2005, "
        "Vandura:v:1981-1995, Savana:v:1996-")),
    "Buick": ("BU", "GM", _m(
        "LeSabre:c:1981-2005, Century:c:1982-2005, Regal:c:1981-2004|2011-2020, Park Avenue:c:1991-2005, "
        "Skylark:c:1981-1998, Riviera:c:1981-1999, Roadmaster:c:1991-1996, LaCrosse:c:2005-2019, "
        "Lucerne:c:2006-2011, Verano:c:2012-2017, Cascada:c:2016-2019, Rendezvous:s:2002-2007, "
        "Rainier:s:2004-2007, Enclave:s:2008-, Encore:s:2013-, Envision:s:2016-, Terraza:v:2005-2007")),
    "Cadillac": ("CA", "GM", _m(
        "DeVille:c:1981-2005, DTS:c:2006-2011, Seville:c:1981-2004, STS:c:2005-2011, Fleetwood:c:1981-1996, "
        "Eldorado:c:1981-2002, Catera:c:1997-2001, CTS:c:2003-2019, ATS:c:2013-2019, XTS:c:2013-2019, "
        "CT4:c:2020-, CT5:c:2020-, CT6:c:2016-2020, XLR:c:2004-2009, ELR:c:2014-2016, Escalade:s:1999-, "
        "Escalade ESV:s:2003-, Escalade EXT:t:2002-2013, SRX:s:2004-2016, XT4:s:2019-, XT5:s:2017-, "
        "XT6:s:2020-")),
    "Pontiac": ("PO", "GM", _m(
        "Grand Prix:c:1981-2008, Grand Am:c:1985-2005, Bonneville:c:1981-2005, Firebird:c:1981-2002, "
        "Sunbird:c:1982-1994, Sunfire:c:1995-2005, 6000:c:1982-1991, Fiero:c:1984-1988, G5:c:2007-2009, "
        "G6:c:2005-2010, G8:c:2008-2009, Vibe:c:2003-2010, Solstice:c:2006-2010, GTO:c:2004-2006, "
        "Aztek:s:2001-2005, Torrent:s:2006-2009, Trans Sport:v:1990-1998, Montana:v:1999-2009")),
    "Oldsmobile": ("OL", "GM", _m(
        "Cutlass / Cutlass Ciera:c:1981-1999, Eighty-Eight:c:1981-1999, Ninety-Eight:c:1981-1996, "
        "Toronado:c:1981-1992, Achieva:c:1992-1998, Aurora:c:1995-1999|2001-2003, Intrigue:c:1998-2002, "
        "Alero:c:1999-2004, Bravada:s:1991-1994|1996-2004, Silhouette:v:1990-2004")),
    "Saturn": ("ST", "GM", _m(
        "S-Series:c:1991-2002, L-Series:c:2000-2005, Ion:c:2003-2007, Aura:c:2007-2009, Sky:c:2007-2010, "
        "Astra:c:2008-2009, Vue:s:2002-2010, Outlook:s:2007-2010, Relay:v:2005-2007")),
    "Hummer": ("HM", "GM", _m("H1:s:1992-2006, H2:s:2003-2009, H3:s:2006-2010, H3T:t:2009-2010")),
    "Lincoln": ("LN", "Ford", _m(
        "Town Car:c:1981-2011, Continental:c:1982-2002|2017-2020, Mark VII:c:1984-1992, Mark VIII:c:1993-1998, "
        "LS:c:2000-2006, Zephyr:c:2006, MKZ:c:2007-2020, MKS:c:2009-2016, Navigator:s:1998-, "
        "Aviator:s:2003-2005|2020-, MKX:s:2007-2018, Nautilus:s:2019-, MKC:s:2015-2019, Corsair:s:2020-, "
        "MKT:s:2010-2019, Blackwood:t:2002, Mark LT:t:2006-2008")),
    "Mercury": ("MC", "Ford", _m(
        "Grand Marquis:c:1983-2011, Sable:c:1986-2005|2008-2009, Topaz:c:1984-1994, Lynx:c:1981-1987, "
        "Cougar:c:1981-1997|1999-2002, Mystique:c:1995-2000, Tracer:c:1988-1999, Milan:c:2006-2011, "
        "Montego:c:2005-2007, Marauder:c:2003-2004, Mountaineer:s:1997-2010, Mariner:s:2005-2011, "
        "Villager:v:1993-2002, Monterey:v:2004-2007")),
    "Dodge": ("DG", "Dodge", _m(
        "Ram 1500 / 150 (to 2010):t:1981-2010, Ram 2500 / 250 (to 2010):t:1981-2010, "
        "Ram 3500 / 350 (to 2010):t:1981-2010, Dakota:t:1987-2011, Ramcharger:s:1981-1993, "
        "Durango:s:1998-2009|2011-, Nitro:s:2007-2011, Journey:s:2009-2020, Aries:c:1981-1989, Omni:c:1981-1990, "
        "Shadow:c:1987-1994, Spirit:c:1989-1995, Stealth:c:1991-1996, Neon:c:1995-2005, Stratus:c:1995-2006, "
        "Intrepid:c:1993-2004, Avenger:c:1995-2000|2008-2014, Caliber:c:2007-2012, Charger:c:1983-1987|2006-2023, "
        "Challenger:c:2008-2023, Magnum:c:2005-2008, Dart:c:2013-2016, Viper:c:1992-2010|2013-2017, "
        "Caravan:v:1984-2007, Grand Caravan:v:1987-2020, Ram Van:v:1981-2003, Sprinter:v:2003-2009")),
    "Ram": ("RAM", "Ram", _m("1500:t:2011-, 2500:t:2011-, 3500:t:2011-, ProMaster:v:2014-, ProMaster City:v:2015-2022")),
    "Jeep": ("JP", "Jeep", _m(
        "CJ:s:1981-1986, Wrangler:s:1987-, Cherokee:s:1984-2001|2014-2023, Grand Cherokee:s:1993-, "
        "Wagoneer:s:1984-1991|2022-, Grand Wagoneer:s:1984-1991|2022-, Comanche:t:1986-1992, Liberty:s:2002-2012, "
        "Compass:s:2007-, Patriot:s:2007-2017, Commander:s:2006-2010, Renegade:s:2015-2023, Gladiator:t:2020-")),
    "Chrysler": ("CHR", "Chrysler", _m(
        "LeBaron:c:1981-1995, New Yorker:c:1981-1996, Fifth Avenue:c:1983-1993, Concorde:c:1993-2004, "
        "LHS:c:1994-1997|1999-2001, Cirrus:c:1995-2000, Sebring:c:1995-2010, 300M:c:1999-2004, 300:c:2005-2023, "
        "200:c:2011-2017, PT Cruiser:c:2001-2010, Crossfire:c:2004-2008, Town & Country:v:1990-2016, "
        "Voyager:v:2000-2003|2020-2025, Pacifica:v:2004-2008|2017-, Aspen:s:2007-2009")),
    "Plymouth": ("PL", "Plymouth", _m(
        "Reliant:c:1981-1989, Horizon:c:1981-1990, Sundance:c:1987-1994, Acclaim:c:1989-1995, Neon:c:1995-2001, "
        "Breeze:c:1996-2000, Prowler:c:1997-2001, Voyager:v:1984-2000, Grand Voyager:v:1987-2000")),
    "Toyota": ("TY", "Toyota", _m(
        "Pickup:t:1981-1995, T100:t:1993-1998, Tacoma:t:1995-, Tundra:t:2000-, 4Runner:s:1984-, "
        "Land Cruiser:s:1981-2021, RAV4:s:1996-, Highlander:s:2001-, Sequoia:s:2001-, FJ Cruiser:s:2007-2014, "
        "Venza:s:2009-2015|2021-2024, C-HR:s:2018-2022, Corolla Cross:s:2022-, Corolla:c:1981-, Camry:c:1983-, "
        "Tercel:c:1981-1999, Cressida:c:1981-1992, Celica:c:1981-2005, Supra:c:1981-1998|2020-, "
        "MR2:c:1985-1989|1991-1995|2000-2005, Paseo:c:1992-1997, Avalon:c:1995-2022, Solara:c:1999-2008, "
        "Echo:c:2000-2005, Prius:c:2001-, Matrix:c:2003-2013, Yaris:c:2007-2020, 86 / GR86:c:2017-, "
        "Previa:v:1991-1997, Sienna:v:1998-")),
    "Lexus": ("LX", "Toyota", _m(
        "ES:c:1990-, LS:c:1990-, SC:c:1992-2010, GS:c:1993-2020, IS:c:2001-, HS:c:2010-2012, CT:c:2011-2017, "
        "RC:c:2015-, LX:s:1996-, RX:s:1999-, GX:s:2003-, NX:s:2015-, UX:s:2019-")),
    "Scion": ("SC", "Toyota", _m(
        "xA:c:2004-2006, xB:c:2004-2015, tC:c:2005-2016, xD:c:2008-2014, iQ:c:2012-2015, FR-S:c:2013-2016, "
        "iA:c:2016, iM:c:2016")),
    "Honda": ("HO", "Honda", _m(
        "Civic:c:1981-, Accord:c:1981-, Prelude:c:1981-2001, CRX:c:1984-1991, del Sol:c:1993-1997, "
        "S2000:c:2000-2009, Insight:c:2000-2006|2010-2014|2019-2022, Fit:c:2007-2020, Clarity:c:2017-2021, "
        "Passport:s:1994-2002|2019-, CR-V:s:1997-, Pilot:s:2003-, Element:s:2003-2011, HR-V:s:2016-, "
        "Ridgeline:t:2006-2014|2017-, Odyssey:v:1995-")),
    "Acura": ("AC", "Honda", _m(
        "Integra:c:1986-2001|2023-, Legend:c:1986-1995, Vigor:c:1992-1994, NSX:c:1991-2005|2017-2022, "
        "TL:c:1996-2014, RL:c:1996-2012, CL:c:1997-1999|2001-2003, RSX:c:2002-2006, TSX:c:2004-2014, "
        "ILX:c:2013-2022, RLX:c:2014-2020, TLX:c:2015-, SLX:s:1996-1999, MDX:s:2001-, RDX:s:2007-, "
        "ZDX:s:2010-2013")),
    "Nissan": ("NI", "Nissan", _m(
        "Altima:c:1993-, Maxima:c:1981-, Sentra:c:1982-, 200SX:c:1995-1998, 350Z:c:2003-2009, 370Z:c:2009-2020, "
        "Versa:c:2007-, Cube:c:2009-2014, GT-R:c:2009-, Frontier:t:1998-, Titan:t:2004-2024, Pathfinder:s:1987-, "
        "Xterra:s:2000-2015, Armada:s:2004-, Murano:s:2003-, Rogue:s:2008-, Juke:s:2011-2017, Kicks:s:2018-, "
        "Quest:v:1993-2002|2004-2009|2011-2017, NV:v:2012-2021, NV200:v:2013-2021")),
    "Infiniti": ("IN", "Nissan", _m(
        "I30:c:1996-2001, I35:c:2002-2004, G35:c:2003-2008, G37:c:2008-2013, M35:c:2006-2010, M45:c:2003-2010, "
        "Q40:c:2015, Q50:c:2014-, Q60:c:2014-2015|2017-2022, Q70:c:2014-2019, QX4:s:1997-2003, FX35:s:2003-2012, "
        "FX45:s:2003-2008, QX56:s:2004-2013, EX35:s:2008-2012, JX35:s:2013, QX50:s:2014-, QX60:s:2014-, "
        "QX70:s:2014-2017, QX80:s:2014-")),
    "Hyundai": ("HY", "Hyundai", _m(
        "Sonata:c:1989-, Elantra:c:1992-, Accent:c:1995-2022, Tiburon:c:1997-2008, Azera:c:2006-2017, "
        "Genesis:c:2009-2016, Veloster:c:2012-2022, Ioniq Hybrid:c:2017-2022, Santa Fe:s:2001-, Tucson:s:2005-, "
        "Veracruz:s:2007-2012, Kona:s:2018-, Palisade:s:2020-, Venue:s:2020-, Santa Cruz:t:2022-, "
        "Entourage:v:2007-2009")),
    "Genesis": ("GN", "Hyundai", _m("G80:c:2017-, G90:c:2017-, G70:c:2019-, GV80:s:2021-, GV70:s:2022-")),
    "Kia": ("KIA", "Kia", _m(
        "Sephia:c:1994-2001, Spectra:c:2000-2009, Rio:c:2001-2023, Optima:c:2001-2020, K5:c:2021-, "
        "Forte:c:2010-, Soul:c:2010-, Cadenza:c:2014-2020, Stinger:c:2018-2023, Sportage:s:1995-2002|2005-, "
        "Sorento:s:2003-, Borrego:s:2009, Niro:s:2017-, Telluride:s:2020-, Seltos:s:2021-, Sedona:v:2002-2021, "
        "Carnival:v:2022-")),
    "Mazda": ("MZ", "Mazda", _m(
        "626:c:1981-2002, Protege:c:1990-2003, MX-5 Miata:c:1990-, Millenia:c:1995-2002, Mazda6:c:2003-2021, "
        "Mazda3:c:2004-, RX-8:c:2004-2011, Mazda2:c:2011-2014, B-Series:t:1981-2009, Tribute:s:2001-2011, "
        "CX-7:s:2007-2012, CX-9:s:2007-2023, CX-5:s:2013-, CX-3:s:2016-2021, CX-30:s:2020-, MPV:v:1989-2006, "
        "Mazda5:v:2006-2015")),
    "Subaru": ("SU", "Subaru", _m(
        "Legacy:c:1990-, Impreza:c:1993-, WRX:c:2002-, BRZ:c:2013-, Outback:s:1995-, Forester:s:1998-, "
        "Baja:t:2003-2006, Tribeca:s:2006-2014, Crosstrek:s:2013-, Ascent:s:2019-")),
    "Mitsubishi": ("MI", "Mitsubishi", _m(
        "Galant:c:1985-2012, Mirage:c:1985-2002|2014-, Eclipse:c:1990-2012, 3000GT:c:1991-1999, "
        "Diamante:c:1992-2004, Lancer:c:2002-2017, Montero:s:1983-2006, Montero Sport:s:1997-2004, "
        "Outlander:s:2003-, Endeavor:s:2004-2011, Outlander Sport:s:2011-, Eclipse Cross:s:2018-, "
        "Raider:t:2006-2009")),
    "Suzuki": ("SZ", "Suzuki", _m(
        "Swift:c:1989-2001, Esteem:c:1995-2002, Aerio:c:2002-2007, Forenza:c:2004-2008, Reno:c:2005-2008, "
        "SX4:c:2007-2013, Kizashi:c:2010-2013, Sidekick:s:1989-1998, Vitara:s:1999-2004, "
        "Grand Vitara:s:1999-2013, XL-7:s:2001-2009, Equator:t:2009-2012")),
    "Isuzu": ("IS", "GM", _m(
        "Trooper:s:1984-2002, Amigo:s:1989-1994|1998-2000, Rodeo:s:1991-2004, Hombre:t:1996-2000, "
        "Axiom:s:2002-2004, Ascender:s:2003-2008, i-Series:t:2006-2008")),
    "Volkswagen": ("VW", "Volkswagen", _m(
        "Jetta:c:1981-, Golf:c:1985-2021, GTI:c:1983-, Rabbit:c:1981-1984|2007-2009, Passat:c:1990-2022, "
        "Cabrio:c:1995-2002, Beetle:c:1998-2019, Phaeton:c:2004-2006, Eos:c:2007-2016, CC:c:2009-2017, "
        "Arteon:c:2019-2023, Touareg:s:2004-2017, Tiguan:s:2009-, Atlas:s:2018-, Taos:s:2022-, "
        "EuroVan:v:1992-2003, Routan:v:2009-2014")),
    "Audi": ("AU", "Volkswagen", _m(
        "A4:c:1996-, A6:c:1995-, A8:c:1997-, TT:c:2000-2023, A3:c:2006-, A5:c:2008-, R8:c:2008-2023, "
        "A7:c:2012-, allroad:s:2001-2005|2013-2016, Q7:s:2007-, Q5:s:2009-, Q3:s:2015-, Q8:s:2019-")),
    "BMW": ("BMW", "BMW", _m(
        "3 Series:c:1981-, 5 Series:c:1981-, 7 Series:c:1981-, 6 Series:c:1981-1989|2004-2019, "
        "8 Series:c:1991-1997|2019-, Z3:c:1996-2002, Z4:c:2003-2016|2019-, 1 Series:c:2008-2013, "
        "2 Series:c:2014-, 4 Series:c:2014-, X5:s:2000-, X3:s:2004-, X6:s:2008-, X1:s:2013-, X4:s:2015-, "
        "X2:s:2018-, X7:s:2019-")),
    "Mini": ("MN", "BMW", _m("Cooper:c:2002-, Clubman:c:2008-, Countryman:s:2011-, Paceman:c:2013-2016")),
    "Mercedes-Benz": ("MB", "Mercedes-Benz", _m(
        "S-Class:c:1981-, SL:c:1981-, E-Class:c:1986-, C-Class:c:1994-, CLK:c:1998-2009, SLK:c:1998-2020, "
        "CLS:c:2006-, CLA:c:2014-, ML / GLE:s:1998-, G-Class:s:2002-, GL / GLS:s:2007-, GLK / GLC:s:2010-, "
        "GLA:s:2015-, Sprinter:v:2010-, Metris:v:2016-2023")),
    "Volvo": ("VO", "Volvo", _m(
        "S90:c:1997-1998|2017-, S70:c:1998-2000, V70:c:1998-2010, C70:c:1998-2013, S80:c:1999-2016, "
        "S40:c:2000-2011, V40:c:2000-2004, S60:c:2001-, V50:c:2005-2011, C30:c:2008-2013, V60:c:2015-, "
        "XC70:s:2003-2016, XC90:s:2003-, XC60:s:2010-, XC40:s:2019-")),
    "Saab": ("SA", "GM", _m("9-3:c:1999-2011, 9-5:c:1999-2011, 9-2X:c:2005-2006, 9-7X:s:2005-2009")),
    "Porsche": ("PR", "Volkswagen", _m(
        "911:c:1981-, Boxster:c:1997-, Cayman:c:2006-, Panamera:c:2010-, Cayenne:s:2003-, Macan:s:2015-")),
    "Jaguar": ("JA", "Jaguar", _m(
        "XJ:c:1981-2019, XK:c:1997-2015, S-Type:c:2000-2008, X-Type:c:2002-2008, XF:c:2009-2024, "
        "F-Type:c:2014-2024, XE:c:2017-2020, F-Pace:s:2017-, E-Pace:s:2018-2024")),
    "Land Rover": ("LR", "Land Rover", _m(
        "Range Rover:s:1987-, Discovery:s:1994-2004|2017-, Defender:s:1993-1997|2020-, Freelander:s:2002-2005, "
        "LR3:s:2005-2009, Range Rover Sport:s:2006-, LR2:s:2008-2015, LR4:s:2010-2016, "
        "Range Rover Evoque:s:2012-, Discovery Sport:s:2015-, Range Rover Velar:s:2018-")),
    "Fiat": ("FI", "Chrysler", _m("500:c:2012-2019, 500L:c:2014-2020, 500X:s:2016-2023, 124 Spider:c:2017-2020")),
}

# Makes whose 1995-and-older vehicles have a blink-code guide (see obd1.py). Saab and Isuzu share GM's
# family for scanning newer models but used their own systems before 1996, so they aren't here.
OBD1_GROUP = {
    "Chevrolet": "GM", "GMC": "GM", "Buick": "GM", "Cadillac": "GM", "Pontiac": "GM", "Oldsmobile": "GM",
    "Ford": "Ford", "Lincoln": "Ford", "Mercury": "Ford",
    "Chrysler": "Chrysler", "Dodge": "Chrysler", "Jeep": "Chrysler", "Plymouth": "Chrysler",
    "Toyota": "Toyota", "Lexus": "Toyota", "Honda": "Honda", "Acura": "Honda",
}

FULL_SUPPORT_FAMILIES = ("Ford", "GM")


def obd1_group(make):
    return OBD1_GROUP.get(make)


def earliest_year(make):
    return OBD1_FIRST_YEAR if obd1_group(make) else FIRST_YEAR


def model_years(make, model):
    """Model years to offer for this make and model, newest first. model '' (Other) = every year."""
    first, last = earliest_year(make), _this_year() + 1
    spec = next((y for name, _k, y in MAKES.get(make, ("", "", []))[2] if name == model), None)
    if not model or spec is None:
        return list(range(last, first - 1, -1))
    years = set()
    for a, b in _ranges(spec):
        years.update(range(max(a, first), min(b, last) + 1))
    return sorted(years, reverse=True)


def years(make=None, model=None):
    if make and model is not None:
        return model_years(make, model)
    first = earliest_year(make) if make else FIRST_YEAR
    return list(range(_this_year() + 1, first - 1, -1))


def models(make):
    """Models that have at least one year this app can read, as [(name, type)]."""
    return [(n, k) for n, k, _y in MAKES[make][2] if model_years(make, n)]


def support_text(make, year=None):
    if year is not None and int(year) < 1996:
        return "Engine codes by blink-code guide" if obd1_group(make) else "Not readable (1995 and older)"
    if MAKES[make][1] in FULL_SUPPORT_FAMILIES:
        return "Engine, ABS and airbag"
    return "Engine codes, some ABS and airbag"


def family_of(make):
    return MAKES.get(make, ("", make, []))[1]
