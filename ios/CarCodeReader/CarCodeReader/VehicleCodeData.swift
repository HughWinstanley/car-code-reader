// Vehicle list + code detail, generated from the Mac app. Do not edit by hand.
import Foundation

struct VModel { let name: String; let minYear: Int; let maxYear: Int }
enum VehicleData {
    static let makes: [String] = [
        "Ford",
        "Chevrolet",
        "GMC",
        "Buick",
        "Cadillac",
        "Pontiac",
        "Oldsmobile",
        "Saturn",
        "Hummer",
        "Lincoln",
        "Mercury",
        "Dodge",
        "Ram",
        "Jeep",
        "Chrysler",
        "Plymouth",
        "Toyota",
        "Lexus",
        "Scion",
        "Honda",
        "Acura",
        "Nissan",
        "Infiniti",
        "Hyundai",
        "Genesis",
        "Kia",
        "Mazda",
        "Subaru",
        "Mitsubishi",
        "Suzuki",
        "Isuzu",
        "Volkswagen",
        "Audi",
        "BMW",
        "Mini",
        "Mercedes-Benz",
        "Volvo",
        "Saab",
        "Porsche",
        "Jaguar",
        "Land Rover",
        "Fiat",
    ]
    static let models: [String: [VModel]] = [
        "Ford": [VModel(name: "F-150", minYear: 1981, maxYear: 2027), VModel(name: "F-250 Super Duty", minYear: 1998, maxYear: 2027), VModel(name: "F-350 Super Duty", minYear: 1998, maxYear: 2027), VModel(name: "F-450 Super Duty", minYear: 2007, maxYear: 2027), VModel(name: "F-250 / F-350 (before Super Duty)", minYear: 1981, maxYear: 2000), VModel(name: "Ranger", minYear: 1982, maxYear: 2027), VModel(name: "Maverick", minYear: 2021, maxYear: 2027), VModel(name: "Explorer", minYear: 1990, maxYear: 2027), VModel(name: "Explorer Sport Trac", minYear: 2000, maxYear: 2011), VModel(name: "Expedition", minYear: 1996, maxYear: 2027), VModel(name: "Excursion", minYear: 1999, maxYear: 2006), VModel(name: "Bronco", minYear: 1981, maxYear: 2027), VModel(name: "Bronco II", minYear: 1983, maxYear: 1991), VModel(name: "Bronco Sport", minYear: 2020, maxYear: 2027), VModel(name: "Escape", minYear: 2000, maxYear: 2027), VModel(name: "Edge", minYear: 2006, maxYear: 2025), VModel(name: "Flex", minYear: 2008, maxYear: 2020), VModel(name: "EcoSport", minYear: 2017, maxYear: 2023), VModel(name: "Freestyle", minYear: 2004, maxYear: 2008), VModel(name: "Mustang", minYear: 1981, maxYear: 2027), VModel(name: "Taurus", minYear: 1985, maxYear: 2020), VModel(name: "Fusion", minYear: 2005, maxYear: 2021), VModel(name: "Focus", minYear: 1999, maxYear: 2019), VModel(name: "Fiesta", minYear: 2010, maxYear: 2020), VModel(name: "Escort", minYear: 1981, maxYear: 2004), VModel(name: "Tempo", minYear: 1983, maxYear: 1995), VModel(name: "Festiva", minYear: 1987, maxYear: 1994), VModel(name: "Contour", minYear: 1994, maxYear: 2001), VModel(name: "Crown Victoria", minYear: 1982, maxYear: 2012), VModel(name: "Five Hundred", minYear: 2004, maxYear: 2008), VModel(name: "Thunderbird", minYear: 1981, maxYear: 2006), VModel(name: "Probe", minYear: 1988, maxYear: 1998), VModel(name: "Aspire", minYear: 1993, maxYear: 1998), VModel(name: "C-Max", minYear: 2012, maxYear: 2019), VModel(name: "GT", minYear: 2004, maxYear: 2023), VModel(name: "Aerostar", minYear: 1985, maxYear: 1998), VModel(name: "Windstar", minYear: 1994, maxYear: 2004), VModel(name: "Freestar", minYear: 2003, maxYear: 2008), VModel(name: "E-Series / Econoline", minYear: 1981, maxYear: 2027), VModel(name: "Transit", minYear: 2014, maxYear: 2027), VModel(name: "Transit Connect", minYear: 2009, maxYear: 2024)],
        "Chevrolet": [VModel(name: "Silverado 1500", minYear: 1998, maxYear: 2027), VModel(name: "Silverado 2500 / 2500HD", minYear: 1998, maxYear: 2027), VModel(name: "Silverado 3500 / 3500HD", minYear: 2000, maxYear: 2027), VModel(name: "C/K 1500", minYear: 1981, maxYear: 2000), VModel(name: "C/K 2500", minYear: 1981, maxYear: 2001), VModel(name: "C/K 3500", minYear: 1981, maxYear: 2001), VModel(name: "S-10", minYear: 1981, maxYear: 2005), VModel(name: "Colorado", minYear: 2003, maxYear: 2027), VModel(name: "Avalanche", minYear: 2001, maxYear: 2014), VModel(name: "SSR", minYear: 2002, maxYear: 2007), VModel(name: "Tahoe", minYear: 1994, maxYear: 2027), VModel(name: "Suburban", minYear: 1981, maxYear: 2027), VModel(name: "Blazer (full-size K5)", minYear: 1981, maxYear: 1995), VModel(name: "Blazer (S-10 Blazer)", minYear: 1982, maxYear: 2006), VModel(name: "Blazer", minYear: 2018, maxYear: 2027), VModel(name: "TrailBlazer", minYear: 2001, maxYear: 2027), VModel(name: "Equinox", minYear: 2004, maxYear: 2027), VModel(name: "Traverse", minYear: 2008, maxYear: 2027), VModel(name: "Trax", minYear: 2014, maxYear: 2027), VModel(name: "Tracker", minYear: 1988, maxYear: 2005), VModel(name: "HHR", minYear: 2005, maxYear: 2012), VModel(name: "Captiva Sport", minYear: 2011, maxYear: 2016), VModel(name: "Malibu", minYear: 1981, maxYear: 2026), VModel(name: "Impala", minYear: 1981, maxYear: 2021), VModel(name: "Monte Carlo", minYear: 1981, maxYear: 2008), VModel(name: "Cavalier", minYear: 1981, maxYear: 2006), VModel(name: "Cobalt", minYear: 2004, maxYear: 2011), VModel(name: "Cruze", minYear: 2010, maxYear: 2020), VModel(name: "Sonic", minYear: 2011, maxYear: 2021), VModel(name: "Aveo", minYear: 2003, maxYear: 2012), VModel(name: "Spark", minYear: 2012, maxYear: 2023), VModel(name: "Camaro", minYear: 1981, maxYear: 2025), VModel(name: "Corvette", minYear: 1981, maxYear: 2027), VModel(name: "Lumina", minYear: 1989, maxYear: 2002), VModel(name: "Celebrity", minYear: 1981, maxYear: 1991), VModel(name: "Beretta", minYear: 1986, maxYear: 1997), VModel(name: "Corsica", minYear: 1986, maxYear: 1997), VModel(name: "Citation", minYear: 1981, maxYear: 1986), VModel(name: "Chevette", minYear: 1981, maxYear: 1988), VModel(name: "Prizm", minYear: 1989, maxYear: 2003), VModel(name: "Metro", minYear: 1988, maxYear: 2002), VModel(name: "Volt", minYear: 2010, maxYear: 2020), VModel(name: "Caprice", minYear: 1981, maxYear: 1997), VModel(name: "Lumina APV", minYear: 1989, maxYear: 1997), VModel(name: "Venture", minYear: 1996, maxYear: 2006), VModel(name: "Uplander", minYear: 2004, maxYear: 2010), VModel(name: "Astro", minYear: 1984, maxYear: 2006), VModel(name: "Chevy Van / G-Series", minYear: 1981, maxYear: 1997), VModel(name: "Express", minYear: 1995, maxYear: 2027), VModel(name: "City Express", minYear: 2014, maxYear: 2019)],
        "GMC": [VModel(name: "Sierra 1500", minYear: 1998, maxYear: 2027), VModel(name: "Sierra 2500 / 2500HD", minYear: 1998, maxYear: 2027), VModel(name: "Sierra 3500 / 3500HD", minYear: 2000, maxYear: 2027), VModel(name: "Sierra C/K 1500 / 2500 / 3500", minYear: 1981, maxYear: 2001), VModel(name: "S-15", minYear: 1981, maxYear: 1991), VModel(name: "Sonoma", minYear: 1990, maxYear: 2005), VModel(name: "Canyon", minYear: 2003, maxYear: 2027), VModel(name: "Yukon", minYear: 1991, maxYear: 2027), VModel(name: "Yukon XL", minYear: 1999, maxYear: 2027), VModel(name: "Suburban (GMC)", minYear: 1981, maxYear: 2000), VModel(name: "Jimmy", minYear: 1981, maxYear: 2006), VModel(name: "Envoy", minYear: 1997, maxYear: 2010), VModel(name: "Acadia", minYear: 2006, maxYear: 2027), VModel(name: "Terrain", minYear: 2009, maxYear: 2027), VModel(name: "Safari", minYear: 1984, maxYear: 2006), VModel(name: "Vandura", minYear: 1981, maxYear: 1996), VModel(name: "Savana", minYear: 1995, maxYear: 2027)],
        "Buick": [VModel(name: "LeSabre", minYear: 1981, maxYear: 2006), VModel(name: "Century", minYear: 1981, maxYear: 2006), VModel(name: "Regal", minYear: 1981, maxYear: 2021), VModel(name: "Park Avenue", minYear: 1990, maxYear: 2006), VModel(name: "Skylark", minYear: 1981, maxYear: 1999), VModel(name: "Riviera", minYear: 1981, maxYear: 2000), VModel(name: "Roadmaster", minYear: 1990, maxYear: 1997), VModel(name: "LaCrosse", minYear: 2004, maxYear: 2020), VModel(name: "Lucerne", minYear: 2005, maxYear: 2012), VModel(name: "Verano", minYear: 2011, maxYear: 2018), VModel(name: "Cascada", minYear: 2015, maxYear: 2020), VModel(name: "Rendezvous", minYear: 2001, maxYear: 2008), VModel(name: "Rainier", minYear: 2003, maxYear: 2008), VModel(name: "Enclave", minYear: 2007, maxYear: 2027), VModel(name: "Encore", minYear: 2012, maxYear: 2027), VModel(name: "Envision", minYear: 2015, maxYear: 2027), VModel(name: "Terraza", minYear: 2004, maxYear: 2008)],
        "Cadillac": [VModel(name: "DeVille", minYear: 1981, maxYear: 2006), VModel(name: "DTS", minYear: 2005, maxYear: 2012), VModel(name: "Seville", minYear: 1981, maxYear: 2005), VModel(name: "STS", minYear: 2004, maxYear: 2012), VModel(name: "Fleetwood", minYear: 1981, maxYear: 1997), VModel(name: "Eldorado", minYear: 1981, maxYear: 2003), VModel(name: "Catera", minYear: 1996, maxYear: 2002), VModel(name: "CTS", minYear: 2002, maxYear: 2020), VModel(name: "ATS", minYear: 2012, maxYear: 2020), VModel(name: "XTS", minYear: 2012, maxYear: 2020), VModel(name: "CT4", minYear: 2019, maxYear: 2027), VModel(name: "CT5", minYear: 2019, maxYear: 2027), VModel(name: "CT6", minYear: 2015, maxYear: 2021), VModel(name: "XLR", minYear: 2003, maxYear: 2010), VModel(name: "ELR", minYear: 2013, maxYear: 2017), VModel(name: "Escalade", minYear: 1998, maxYear: 2027), VModel(name: "Escalade ESV", minYear: 2002, maxYear: 2027), VModel(name: "Escalade EXT", minYear: 2001, maxYear: 2014), VModel(name: "SRX", minYear: 2003, maxYear: 2017), VModel(name: "XT4", minYear: 2018, maxYear: 2027), VModel(name: "XT5", minYear: 2016, maxYear: 2027), VModel(name: "XT6", minYear: 2019, maxYear: 2027)],
        "Pontiac": [VModel(name: "Grand Prix", minYear: 1981, maxYear: 2009), VModel(name: "Grand Am", minYear: 1984, maxYear: 2006), VModel(name: "Bonneville", minYear: 1981, maxYear: 2006), VModel(name: "Firebird", minYear: 1981, maxYear: 2003), VModel(name: "Sunbird", minYear: 1981, maxYear: 1995), VModel(name: "Sunfire", minYear: 1994, maxYear: 2006), VModel(name: "6000", minYear: 1981, maxYear: 1992), VModel(name: "Fiero", minYear: 1983, maxYear: 1989), VModel(name: "G5", minYear: 2006, maxYear: 2010), VModel(name: "G6", minYear: 2004, maxYear: 2011), VModel(name: "G8", minYear: 2007, maxYear: 2010), VModel(name: "Vibe", minYear: 2002, maxYear: 2011), VModel(name: "Solstice", minYear: 2005, maxYear: 2011), VModel(name: "GTO", minYear: 2003, maxYear: 2007), VModel(name: "Aztek", minYear: 2000, maxYear: 2006), VModel(name: "Torrent", minYear: 2005, maxYear: 2010), VModel(name: "Trans Sport", minYear: 1989, maxYear: 1999), VModel(name: "Montana", minYear: 1998, maxYear: 2010)],
        "Oldsmobile": [VModel(name: "Cutlass / Cutlass Ciera", minYear: 1981, maxYear: 2000), VModel(name: "Eighty-Eight", minYear: 1981, maxYear: 2000), VModel(name: "Ninety-Eight", minYear: 1981, maxYear: 1997), VModel(name: "Toronado", minYear: 1981, maxYear: 1993), VModel(name: "Achieva", minYear: 1991, maxYear: 1999), VModel(name: "Aurora", minYear: 1994, maxYear: 2004), VModel(name: "Intrigue", minYear: 1997, maxYear: 2003), VModel(name: "Alero", minYear: 1998, maxYear: 2005), VModel(name: "Bravada", minYear: 1990, maxYear: 2005), VModel(name: "Silhouette", minYear: 1989, maxYear: 2005)],
        "Saturn": [VModel(name: "S-Series", minYear: 1996, maxYear: 2003), VModel(name: "L-Series", minYear: 1999, maxYear: 2006), VModel(name: "Ion", minYear: 2002, maxYear: 2008), VModel(name: "Aura", minYear: 2006, maxYear: 2010), VModel(name: "Sky", minYear: 2006, maxYear: 2011), VModel(name: "Astra", minYear: 2007, maxYear: 2010), VModel(name: "Vue", minYear: 2001, maxYear: 2011), VModel(name: "Outlook", minYear: 2006, maxYear: 2011), VModel(name: "Relay", minYear: 2004, maxYear: 2008)],
        "Hummer": [VModel(name: "H1", minYear: 1996, maxYear: 2007), VModel(name: "H2", minYear: 2002, maxYear: 2010), VModel(name: "H3", minYear: 2005, maxYear: 2011), VModel(name: "H3T", minYear: 2008, maxYear: 2011)],
        "Lincoln": [VModel(name: "Town Car", minYear: 1981, maxYear: 2012), VModel(name: "Continental", minYear: 1981, maxYear: 2021), VModel(name: "Mark VII", minYear: 1983, maxYear: 1993), VModel(name: "Mark VIII", minYear: 1992, maxYear: 1999), VModel(name: "LS", minYear: 1999, maxYear: 2007), VModel(name: "Zephyr", minYear: 2005, maxYear: 2007), VModel(name: "MKZ", minYear: 2006, maxYear: 2021), VModel(name: "MKS", minYear: 2008, maxYear: 2017), VModel(name: "Navigator", minYear: 1997, maxYear: 2027), VModel(name: "Aviator", minYear: 2002, maxYear: 2027), VModel(name: "MKX", minYear: 2006, maxYear: 2019), VModel(name: "Nautilus", minYear: 2018, maxYear: 2027), VModel(name: "MKC", minYear: 2014, maxYear: 2020), VModel(name: "Corsair", minYear: 2019, maxYear: 2027), VModel(name: "MKT", minYear: 2009, maxYear: 2020), VModel(name: "Blackwood", minYear: 2001, maxYear: 2003), VModel(name: "Mark LT", minYear: 2005, maxYear: 2009)],
        "Mercury": [VModel(name: "Grand Marquis", minYear: 1982, maxYear: 2012), VModel(name: "Sable", minYear: 1985, maxYear: 2010), VModel(name: "Topaz", minYear: 1983, maxYear: 1995), VModel(name: "Lynx", minYear: 1981, maxYear: 1988), VModel(name: "Cougar", minYear: 1981, maxYear: 2003), VModel(name: "Mystique", minYear: 1994, maxYear: 2001), VModel(name: "Tracer", minYear: 1987, maxYear: 2000), VModel(name: "Milan", minYear: 2005, maxYear: 2012), VModel(name: "Montego", minYear: 2004, maxYear: 2008), VModel(name: "Marauder", minYear: 2002, maxYear: 2005), VModel(name: "Mountaineer", minYear: 1996, maxYear: 2011), VModel(name: "Mariner", minYear: 2004, maxYear: 2012), VModel(name: "Villager", minYear: 1992, maxYear: 2003), VModel(name: "Monterey", minYear: 2003, maxYear: 2008)],
        "Dodge": [VModel(name: "Ram 1500 / 150 (to 2010)", minYear: 1981, maxYear: 2011), VModel(name: "Ram 2500 / 250 (to 2010)", minYear: 1981, maxYear: 2011), VModel(name: "Ram 3500 / 350 (to 2010)", minYear: 1981, maxYear: 2011), VModel(name: "Dakota", minYear: 1986, maxYear: 2012), VModel(name: "Ramcharger", minYear: 1981, maxYear: 1994), VModel(name: "Durango", minYear: 1997, maxYear: 2027), VModel(name: "Nitro", minYear: 2006, maxYear: 2012), VModel(name: "Journey", minYear: 2008, maxYear: 2021), VModel(name: "Aries", minYear: 1981, maxYear: 1990), VModel(name: "Omni", minYear: 1981, maxYear: 1991), VModel(name: "Shadow", minYear: 1986, maxYear: 1995), VModel(name: "Spirit", minYear: 1988, maxYear: 1996), VModel(name: "Stealth", minYear: 1990, maxYear: 1997), VModel(name: "Neon", minYear: 1994, maxYear: 2006), VModel(name: "Stratus", minYear: 1994, maxYear: 2007), VModel(name: "Intrepid", minYear: 1992, maxYear: 2005), VModel(name: "Avenger", minYear: 1994, maxYear: 2015), VModel(name: "Caliber", minYear: 2006, maxYear: 2013), VModel(name: "Charger", minYear: 1982, maxYear: 2024), VModel(name: "Challenger", minYear: 2007, maxYear: 2024), VModel(name: "Magnum", minYear: 2004, maxYear: 2009), VModel(name: "Dart", minYear: 2012, maxYear: 2017), VModel(name: "Viper", minYear: 1991, maxYear: 2018), VModel(name: "Caravan", minYear: 1983, maxYear: 2008), VModel(name: "Grand Caravan", minYear: 1986, maxYear: 2021), VModel(name: "Ram Van", minYear: 1981, maxYear: 2004), VModel(name: "Sprinter", minYear: 2002, maxYear: 2010)],
        "Ram": [VModel(name: "1500", minYear: 2010, maxYear: 2027), VModel(name: "2500", minYear: 2010, maxYear: 2027), VModel(name: "3500", minYear: 2010, maxYear: 2027), VModel(name: "ProMaster", minYear: 2013, maxYear: 2027), VModel(name: "ProMaster City", minYear: 2014, maxYear: 2023)],
        "Jeep": [VModel(name: "CJ", minYear: 1981, maxYear: 1987), VModel(name: "Wrangler", minYear: 1986, maxYear: 2027), VModel(name: "Cherokee", minYear: 1983, maxYear: 2024), VModel(name: "Grand Cherokee", minYear: 1992, maxYear: 2027), VModel(name: "Wagoneer", minYear: 1983, maxYear: 2027), VModel(name: "Grand Wagoneer", minYear: 1983, maxYear: 2027), VModel(name: "Comanche", minYear: 1985, maxYear: 1993), VModel(name: "Liberty", minYear: 2001, maxYear: 2013), VModel(name: "Compass", minYear: 2006, maxYear: 2027), VModel(name: "Patriot", minYear: 2006, maxYear: 2018), VModel(name: "Commander", minYear: 2005, maxYear: 2011), VModel(name: "Renegade", minYear: 2014, maxYear: 2024), VModel(name: "Gladiator", minYear: 2019, maxYear: 2027)],
        "Chrysler": [VModel(name: "LeBaron", minYear: 1981, maxYear: 1996), VModel(name: "New Yorker", minYear: 1981, maxYear: 1997), VModel(name: "Fifth Avenue", minYear: 1982, maxYear: 1994), VModel(name: "Concorde", minYear: 1992, maxYear: 2005), VModel(name: "LHS", minYear: 1993, maxYear: 2002), VModel(name: "Cirrus", minYear: 1994, maxYear: 2001), VModel(name: "Sebring", minYear: 1994, maxYear: 2011), VModel(name: "300M", minYear: 1998, maxYear: 2005), VModel(name: "300", minYear: 2004, maxYear: 2024), VModel(name: "200", minYear: 2010, maxYear: 2018), VModel(name: "PT Cruiser", minYear: 2000, maxYear: 2011), VModel(name: "Crossfire", minYear: 2003, maxYear: 2009), VModel(name: "Town & Country", minYear: 1989, maxYear: 2017), VModel(name: "Voyager", minYear: 1999, maxYear: 2026), VModel(name: "Pacifica", minYear: 2003, maxYear: 2027), VModel(name: "Aspen", minYear: 2006, maxYear: 2010)],
        "Plymouth": [VModel(name: "Reliant", minYear: 1981, maxYear: 1990), VModel(name: "Horizon", minYear: 1981, maxYear: 1991), VModel(name: "Sundance", minYear: 1986, maxYear: 1995), VModel(name: "Acclaim", minYear: 1988, maxYear: 1996), VModel(name: "Neon", minYear: 1994, maxYear: 2002), VModel(name: "Breeze", minYear: 1995, maxYear: 2001), VModel(name: "Prowler", minYear: 1996, maxYear: 2002), VModel(name: "Voyager", minYear: 1983, maxYear: 2001), VModel(name: "Grand Voyager", minYear: 1986, maxYear: 2001)],
        "Toyota": [VModel(name: "Pickup", minYear: 1981, maxYear: 1996), VModel(name: "T100", minYear: 1992, maxYear: 1999), VModel(name: "Tacoma", minYear: 1994, maxYear: 2027), VModel(name: "Tundra", minYear: 1999, maxYear: 2027), VModel(name: "4Runner", minYear: 1983, maxYear: 2027), VModel(name: "Land Cruiser", minYear: 1981, maxYear: 2022), VModel(name: "RAV4", minYear: 1995, maxYear: 2027), VModel(name: "Highlander", minYear: 2000, maxYear: 2027), VModel(name: "Sequoia", minYear: 2000, maxYear: 2027), VModel(name: "FJ Cruiser", minYear: 2006, maxYear: 2015), VModel(name: "Venza", minYear: 2008, maxYear: 2025), VModel(name: "C-HR", minYear: 2017, maxYear: 2023), VModel(name: "Corolla Cross", minYear: 2021, maxYear: 2027), VModel(name: "Corolla", minYear: 1981, maxYear: 2027), VModel(name: "Camry", minYear: 1982, maxYear: 2027), VModel(name: "Tercel", minYear: 1981, maxYear: 2000), VModel(name: "Cressida", minYear: 1981, maxYear: 1993), VModel(name: "Celica", minYear: 1981, maxYear: 2006), VModel(name: "Supra", minYear: 1981, maxYear: 2027), VModel(name: "MR2", minYear: 1984, maxYear: 2006), VModel(name: "Paseo", minYear: 1991, maxYear: 1998), VModel(name: "Avalon", minYear: 1994, maxYear: 2023), VModel(name: "Solara", minYear: 1998, maxYear: 2009), VModel(name: "Echo", minYear: 1999, maxYear: 2006), VModel(name: "Prius", minYear: 2000, maxYear: 2027), VModel(name: "Matrix", minYear: 2002, maxYear: 2014), VModel(name: "Yaris", minYear: 2006, maxYear: 2021), VModel(name: "86 / GR86", minYear: 2016, maxYear: 2027), VModel(name: "Previa", minYear: 1990, maxYear: 1998), VModel(name: "Sienna", minYear: 1997, maxYear: 2027)],
        "Lexus": [VModel(name: "ES", minYear: 1989, maxYear: 2027), VModel(name: "LS", minYear: 1989, maxYear: 2027), VModel(name: "SC", minYear: 1991, maxYear: 2011), VModel(name: "GS", minYear: 1992, maxYear: 2021), VModel(name: "IS", minYear: 2000, maxYear: 2027), VModel(name: "HS", minYear: 2009, maxYear: 2013), VModel(name: "CT", minYear: 2010, maxYear: 2018), VModel(name: "RC", minYear: 2014, maxYear: 2027), VModel(name: "LX", minYear: 1995, maxYear: 2027), VModel(name: "RX", minYear: 1998, maxYear: 2027), VModel(name: "GX", minYear: 2002, maxYear: 2027), VModel(name: "NX", minYear: 2014, maxYear: 2027), VModel(name: "UX", minYear: 2018, maxYear: 2027)],
        "Scion": [VModel(name: "xA", minYear: 2003, maxYear: 2007), VModel(name: "xB", minYear: 2003, maxYear: 2016), VModel(name: "tC", minYear: 2004, maxYear: 2017), VModel(name: "xD", minYear: 2007, maxYear: 2015), VModel(name: "iQ", minYear: 2011, maxYear: 2016), VModel(name: "FR-S", minYear: 2012, maxYear: 2017), VModel(name: "iA", minYear: 2015, maxYear: 2017), VModel(name: "iM", minYear: 2015, maxYear: 2017)],
        "Honda": [VModel(name: "Civic", minYear: 1981, maxYear: 2027), VModel(name: "Accord", minYear: 1981, maxYear: 2027), VModel(name: "Prelude", minYear: 1981, maxYear: 2002), VModel(name: "CRX", minYear: 1983, maxYear: 1992), VModel(name: "del Sol", minYear: 1992, maxYear: 1998), VModel(name: "S2000", minYear: 1999, maxYear: 2010), VModel(name: "Insight", minYear: 1999, maxYear: 2023), VModel(name: "Fit", minYear: 2006, maxYear: 2021), VModel(name: "Clarity", minYear: 2016, maxYear: 2022), VModel(name: "Passport", minYear: 1993, maxYear: 2027), VModel(name: "CR-V", minYear: 1996, maxYear: 2027), VModel(name: "Pilot", minYear: 2002, maxYear: 2027), VModel(name: "Element", minYear: 2002, maxYear: 2012), VModel(name: "HR-V", minYear: 2015, maxYear: 2027), VModel(name: "Ridgeline", minYear: 2005, maxYear: 2027), VModel(name: "Odyssey", minYear: 1994, maxYear: 2027)],
        "Acura": [VModel(name: "Integra", minYear: 1985, maxYear: 2027), VModel(name: "Legend", minYear: 1985, maxYear: 1996), VModel(name: "Vigor", minYear: 1991, maxYear: 1995), VModel(name: "NSX", minYear: 1990, maxYear: 2023), VModel(name: "TL", minYear: 1995, maxYear: 2015), VModel(name: "RL", minYear: 1995, maxYear: 2013), VModel(name: "CL", minYear: 1996, maxYear: 2004), VModel(name: "RSX", minYear: 2001, maxYear: 2007), VModel(name: "TSX", minYear: 2003, maxYear: 2015), VModel(name: "ILX", minYear: 2012, maxYear: 2023), VModel(name: "RLX", minYear: 2013, maxYear: 2021), VModel(name: "TLX", minYear: 2014, maxYear: 2027), VModel(name: "SLX", minYear: 1995, maxYear: 2000), VModel(name: "MDX", minYear: 2000, maxYear: 2027), VModel(name: "RDX", minYear: 2006, maxYear: 2027), VModel(name: "ZDX", minYear: 2009, maxYear: 2014)],
        "Nissan": [VModel(name: "Altima", minYear: 1996, maxYear: 2027), VModel(name: "Maxima", minYear: 1996, maxYear: 2027), VModel(name: "Sentra", minYear: 1996, maxYear: 2027), VModel(name: "200SX", minYear: 1996, maxYear: 1999), VModel(name: "350Z", minYear: 2002, maxYear: 2010), VModel(name: "370Z", minYear: 2008, maxYear: 2021), VModel(name: "Versa", minYear: 2006, maxYear: 2027), VModel(name: "Cube", minYear: 2008, maxYear: 2015), VModel(name: "GT-R", minYear: 2008, maxYear: 2027), VModel(name: "Frontier", minYear: 1997, maxYear: 2027), VModel(name: "Titan", minYear: 2003, maxYear: 2025), VModel(name: "Pathfinder", minYear: 1996, maxYear: 2027), VModel(name: "Xterra", minYear: 1999, maxYear: 2016), VModel(name: "Armada", minYear: 2003, maxYear: 2027), VModel(name: "Murano", minYear: 2002, maxYear: 2027), VModel(name: "Rogue", minYear: 2007, maxYear: 2027), VModel(name: "Juke", minYear: 2010, maxYear: 2018), VModel(name: "Kicks", minYear: 2017, maxYear: 2027), VModel(name: "Quest", minYear: 1996, maxYear: 2018), VModel(name: "NV", minYear: 2011, maxYear: 2022), VModel(name: "NV200", minYear: 2012, maxYear: 2022)],
        "Infiniti": [VModel(name: "I30", minYear: 1996, maxYear: 2002), VModel(name: "I35", minYear: 2001, maxYear: 2005), VModel(name: "G35", minYear: 2002, maxYear: 2009), VModel(name: "G37", minYear: 2007, maxYear: 2014), VModel(name: "M35", minYear: 2005, maxYear: 2011), VModel(name: "M45", minYear: 2002, maxYear: 2011), VModel(name: "Q40", minYear: 2014, maxYear: 2016), VModel(name: "Q50", minYear: 2013, maxYear: 2027), VModel(name: "Q60", minYear: 2013, maxYear: 2023), VModel(name: "Q70", minYear: 2013, maxYear: 2020), VModel(name: "QX4", minYear: 1996, maxYear: 2004), VModel(name: "FX35", minYear: 2002, maxYear: 2013), VModel(name: "FX45", minYear: 2002, maxYear: 2009), VModel(name: "QX56", minYear: 2003, maxYear: 2014), VModel(name: "EX35", minYear: 2007, maxYear: 2013), VModel(name: "JX35", minYear: 2012, maxYear: 2014), VModel(name: "QX50", minYear: 2013, maxYear: 2027), VModel(name: "QX60", minYear: 2013, maxYear: 2027), VModel(name: "QX70", minYear: 2013, maxYear: 2018), VModel(name: "QX80", minYear: 2013, maxYear: 2027)],
        "Hyundai": [VModel(name: "Sonata", minYear: 1996, maxYear: 2027), VModel(name: "Elantra", minYear: 1996, maxYear: 2027), VModel(name: "Accent", minYear: 1996, maxYear: 2023), VModel(name: "Tiburon", minYear: 1996, maxYear: 2009), VModel(name: "Azera", minYear: 2005, maxYear: 2018), VModel(name: "Genesis", minYear: 2008, maxYear: 2017), VModel(name: "Veloster", minYear: 2011, maxYear: 2023), VModel(name: "Ioniq Hybrid", minYear: 2016, maxYear: 2023), VModel(name: "Santa Fe", minYear: 2000, maxYear: 2027), VModel(name: "Tucson", minYear: 2004, maxYear: 2027), VModel(name: "Veracruz", minYear: 2006, maxYear: 2013), VModel(name: "Kona", minYear: 2017, maxYear: 2027), VModel(name: "Palisade", minYear: 2019, maxYear: 2027), VModel(name: "Venue", minYear: 2019, maxYear: 2027), VModel(name: "Santa Cruz", minYear: 2021, maxYear: 2027), VModel(name: "Entourage", minYear: 2006, maxYear: 2010)],
        "Genesis": [VModel(name: "G80", minYear: 2016, maxYear: 2027), VModel(name: "G90", minYear: 2016, maxYear: 2027), VModel(name: "G70", minYear: 2018, maxYear: 2027), VModel(name: "GV80", minYear: 2020, maxYear: 2027), VModel(name: "GV70", minYear: 2021, maxYear: 2027)],
        "Kia": [VModel(name: "Sephia", minYear: 1996, maxYear: 2002), VModel(name: "Spectra", minYear: 1999, maxYear: 2010), VModel(name: "Rio", minYear: 2000, maxYear: 2024), VModel(name: "Optima", minYear: 2000, maxYear: 2021), VModel(name: "K5", minYear: 2020, maxYear: 2027), VModel(name: "Forte", minYear: 2009, maxYear: 2027), VModel(name: "Soul", minYear: 2009, maxYear: 2027), VModel(name: "Cadenza", minYear: 2013, maxYear: 2021), VModel(name: "Stinger", minYear: 2017, maxYear: 2024), VModel(name: "Sportage", minYear: 1996, maxYear: 2027), VModel(name: "Sorento", minYear: 2002, maxYear: 2027), VModel(name: "Borrego", minYear: 2008, maxYear: 2010), VModel(name: "Niro", minYear: 2016, maxYear: 2027), VModel(name: "Telluride", minYear: 2019, maxYear: 2027), VModel(name: "Seltos", minYear: 2020, maxYear: 2027), VModel(name: "Sedona", minYear: 2001, maxYear: 2022), VModel(name: "Carnival", minYear: 2021, maxYear: 2027)],
        "Mazda": [VModel(name: "626", minYear: 1996, maxYear: 2003), VModel(name: "Protege", minYear: 1996, maxYear: 2004), VModel(name: "MX-5 Miata", minYear: 1996, maxYear: 2027), VModel(name: "Millenia", minYear: 1996, maxYear: 2003), VModel(name: "Mazda6", minYear: 2002, maxYear: 2022), VModel(name: "Mazda3", minYear: 2003, maxYear: 2027), VModel(name: "RX-8", minYear: 2003, maxYear: 2012), VModel(name: "Mazda2", minYear: 2010, maxYear: 2015), VModel(name: "B-Series", minYear: 1996, maxYear: 2010), VModel(name: "Tribute", minYear: 2000, maxYear: 2012), VModel(name: "CX-7", minYear: 2006, maxYear: 2013), VModel(name: "CX-9", minYear: 2006, maxYear: 2024), VModel(name: "CX-5", minYear: 2012, maxYear: 2027), VModel(name: "CX-3", minYear: 2015, maxYear: 2022), VModel(name: "CX-30", minYear: 2019, maxYear: 2027), VModel(name: "MPV", minYear: 1996, maxYear: 2007), VModel(name: "Mazda5", minYear: 2005, maxYear: 2016)],
        "Subaru": [VModel(name: "Legacy", minYear: 1996, maxYear: 2027), VModel(name: "Impreza", minYear: 1996, maxYear: 2027), VModel(name: "WRX", minYear: 2001, maxYear: 2027), VModel(name: "BRZ", minYear: 2012, maxYear: 2027), VModel(name: "Outback", minYear: 1996, maxYear: 2027), VModel(name: "Forester", minYear: 1997, maxYear: 2027), VModel(name: "Baja", minYear: 2002, maxYear: 2007), VModel(name: "Tribeca", minYear: 2005, maxYear: 2015), VModel(name: "Crosstrek", minYear: 2012, maxYear: 2027), VModel(name: "Ascent", minYear: 2018, maxYear: 2027)],
        "Mitsubishi": [VModel(name: "Galant", minYear: 1996, maxYear: 2013), VModel(name: "Mirage", minYear: 1996, maxYear: 2027), VModel(name: "Eclipse", minYear: 1996, maxYear: 2013), VModel(name: "3000GT", minYear: 1996, maxYear: 2000), VModel(name: "Diamante", minYear: 1996, maxYear: 2005), VModel(name: "Lancer", minYear: 2001, maxYear: 2018), VModel(name: "Montero", minYear: 1996, maxYear: 2007), VModel(name: "Montero Sport", minYear: 1996, maxYear: 2005), VModel(name: "Outlander", minYear: 2002, maxYear: 2027), VModel(name: "Endeavor", minYear: 2003, maxYear: 2012), VModel(name: "Outlander Sport", minYear: 2010, maxYear: 2027), VModel(name: "Eclipse Cross", minYear: 2017, maxYear: 2027), VModel(name: "Raider", minYear: 2005, maxYear: 2010)],
        "Suzuki": [VModel(name: "Swift", minYear: 1996, maxYear: 2002), VModel(name: "Esteem", minYear: 1996, maxYear: 2003), VModel(name: "Aerio", minYear: 2001, maxYear: 2008), VModel(name: "Forenza", minYear: 2003, maxYear: 2009), VModel(name: "Reno", minYear: 2004, maxYear: 2009), VModel(name: "SX4", minYear: 2006, maxYear: 2014), VModel(name: "Kizashi", minYear: 2009, maxYear: 2014), VModel(name: "Sidekick", minYear: 1996, maxYear: 1999), VModel(name: "Vitara", minYear: 1998, maxYear: 2005), VModel(name: "Grand Vitara", minYear: 1998, maxYear: 2014), VModel(name: "XL-7", minYear: 2000, maxYear: 2010), VModel(name: "Equator", minYear: 2008, maxYear: 2013)],
        "Isuzu": [VModel(name: "Trooper", minYear: 1996, maxYear: 2003), VModel(name: "Amigo", minYear: 1997, maxYear: 2001), VModel(name: "Rodeo", minYear: 1996, maxYear: 2005), VModel(name: "Hombre", minYear: 1996, maxYear: 2001), VModel(name: "Axiom", minYear: 2001, maxYear: 2005), VModel(name: "Ascender", minYear: 2002, maxYear: 2009), VModel(name: "i-Series", minYear: 2005, maxYear: 2009)],
        "Volkswagen": [VModel(name: "Jetta", minYear: 1996, maxYear: 2027), VModel(name: "Golf", minYear: 1996, maxYear: 2022), VModel(name: "GTI", minYear: 1996, maxYear: 2027), VModel(name: "Rabbit", minYear: 2006, maxYear: 2010), VModel(name: "Passat", minYear: 1996, maxYear: 2023), VModel(name: "Cabrio", minYear: 1996, maxYear: 2003), VModel(name: "Beetle", minYear: 1997, maxYear: 2020), VModel(name: "Phaeton", minYear: 2003, maxYear: 2007), VModel(name: "Eos", minYear: 2006, maxYear: 2017), VModel(name: "CC", minYear: 2008, maxYear: 2018), VModel(name: "Arteon", minYear: 2018, maxYear: 2024), VModel(name: "Touareg", minYear: 2003, maxYear: 2018), VModel(name: "Tiguan", minYear: 2008, maxYear: 2027), VModel(name: "Atlas", minYear: 2017, maxYear: 2027), VModel(name: "Taos", minYear: 2021, maxYear: 2027), VModel(name: "EuroVan", minYear: 1996, maxYear: 2004), VModel(name: "Routan", minYear: 2008, maxYear: 2015)],
        "Audi": [VModel(name: "A4", minYear: 1996, maxYear: 2027), VModel(name: "A6", minYear: 1996, maxYear: 2027), VModel(name: "A8", minYear: 1996, maxYear: 2027), VModel(name: "TT", minYear: 1999, maxYear: 2024), VModel(name: "A3", minYear: 2005, maxYear: 2027), VModel(name: "A5", minYear: 2007, maxYear: 2027), VModel(name: "R8", minYear: 2007, maxYear: 2024), VModel(name: "A7", minYear: 2011, maxYear: 2027), VModel(name: "allroad", minYear: 2000, maxYear: 2017), VModel(name: "Q7", minYear: 2006, maxYear: 2027), VModel(name: "Q5", minYear: 2008, maxYear: 2027), VModel(name: "Q3", minYear: 2014, maxYear: 2027), VModel(name: "Q8", minYear: 2018, maxYear: 2027)],
        "BMW": [VModel(name: "3 Series", minYear: 1996, maxYear: 2027), VModel(name: "5 Series", minYear: 1996, maxYear: 2027), VModel(name: "7 Series", minYear: 1996, maxYear: 2027), VModel(name: "6 Series", minYear: 2003, maxYear: 2020), VModel(name: "8 Series", minYear: 1996, maxYear: 2027), VModel(name: "Z3", minYear: 1996, maxYear: 2003), VModel(name: "Z4", minYear: 2002, maxYear: 2027), VModel(name: "1 Series", minYear: 2007, maxYear: 2014), VModel(name: "2 Series", minYear: 2013, maxYear: 2027), VModel(name: "4 Series", minYear: 2013, maxYear: 2027), VModel(name: "X5", minYear: 1999, maxYear: 2027), VModel(name: "X3", minYear: 2003, maxYear: 2027), VModel(name: "X6", minYear: 2007, maxYear: 2027), VModel(name: "X1", minYear: 2012, maxYear: 2027), VModel(name: "X4", minYear: 2014, maxYear: 2027), VModel(name: "X2", minYear: 2017, maxYear: 2027), VModel(name: "X7", minYear: 2018, maxYear: 2027)],
        "Mini": [VModel(name: "Cooper", minYear: 2001, maxYear: 2027), VModel(name: "Clubman", minYear: 2007, maxYear: 2027), VModel(name: "Countryman", minYear: 2010, maxYear: 2027), VModel(name: "Paceman", minYear: 2012, maxYear: 2017)],
        "Mercedes-Benz": [VModel(name: "S-Class", minYear: 1996, maxYear: 2027), VModel(name: "SL", minYear: 1996, maxYear: 2027), VModel(name: "E-Class", minYear: 1996, maxYear: 2027), VModel(name: "C-Class", minYear: 1996, maxYear: 2027), VModel(name: "CLK", minYear: 1997, maxYear: 2010), VModel(name: "SLK", minYear: 1997, maxYear: 2021), VModel(name: "CLS", minYear: 2005, maxYear: 2027), VModel(name: "CLA", minYear: 2013, maxYear: 2027), VModel(name: "ML / GLE", minYear: 1997, maxYear: 2027), VModel(name: "G-Class", minYear: 2001, maxYear: 2027), VModel(name: "GL / GLS", minYear: 2006, maxYear: 2027), VModel(name: "GLK / GLC", minYear: 2009, maxYear: 2027), VModel(name: "GLA", minYear: 2014, maxYear: 2027), VModel(name: "Sprinter", minYear: 2009, maxYear: 2027), VModel(name: "Metris", minYear: 2015, maxYear: 2024)],
        "Volvo": [VModel(name: "S90", minYear: 1996, maxYear: 2027), VModel(name: "S70", minYear: 1997, maxYear: 2001), VModel(name: "V70", minYear: 1997, maxYear: 2011), VModel(name: "C70", minYear: 1997, maxYear: 2014), VModel(name: "S80", minYear: 1998, maxYear: 2017), VModel(name: "S40", minYear: 1999, maxYear: 2012), VModel(name: "V40", minYear: 1999, maxYear: 2005), VModel(name: "S60", minYear: 2000, maxYear: 2027), VModel(name: "V50", minYear: 2004, maxYear: 2012), VModel(name: "C30", minYear: 2007, maxYear: 2014), VModel(name: "V60", minYear: 2014, maxYear: 2027), VModel(name: "XC70", minYear: 2002, maxYear: 2017), VModel(name: "XC90", minYear: 2002, maxYear: 2027), VModel(name: "XC60", minYear: 2009, maxYear: 2027), VModel(name: "XC40", minYear: 2018, maxYear: 2027)],
        "Saab": [VModel(name: "9-3", minYear: 1998, maxYear: 2012), VModel(name: "9-5", minYear: 1998, maxYear: 2012), VModel(name: "9-2X", minYear: 2004, maxYear: 2007), VModel(name: "9-7X", minYear: 2004, maxYear: 2010)],
        "Porsche": [VModel(name: "911", minYear: 1996, maxYear: 2027), VModel(name: "Boxster", minYear: 1996, maxYear: 2027), VModel(name: "Cayman", minYear: 2005, maxYear: 2027), VModel(name: "Panamera", minYear: 2009, maxYear: 2027), VModel(name: "Cayenne", minYear: 2002, maxYear: 2027), VModel(name: "Macan", minYear: 2014, maxYear: 2027)],
        "Jaguar": [VModel(name: "XJ", minYear: 1996, maxYear: 2020), VModel(name: "XK", minYear: 1996, maxYear: 2016), VModel(name: "S-Type", minYear: 1999, maxYear: 2009), VModel(name: "X-Type", minYear: 2001, maxYear: 2009), VModel(name: "XF", minYear: 2008, maxYear: 2025), VModel(name: "F-Type", minYear: 2013, maxYear: 2025), VModel(name: "XE", minYear: 2016, maxYear: 2021), VModel(name: "F-Pace", minYear: 2016, maxYear: 2027), VModel(name: "E-Pace", minYear: 2017, maxYear: 2025)],
        "Land Rover": [VModel(name: "Range Rover", minYear: 1996, maxYear: 2027), VModel(name: "Discovery", minYear: 1996, maxYear: 2027), VModel(name: "Defender", minYear: 1996, maxYear: 2027), VModel(name: "Freelander", minYear: 2001, maxYear: 2006), VModel(name: "LR3", minYear: 2004, maxYear: 2010), VModel(name: "Range Rover Sport", minYear: 2005, maxYear: 2027), VModel(name: "LR2", minYear: 2007, maxYear: 2016), VModel(name: "LR4", minYear: 2009, maxYear: 2017), VModel(name: "Range Rover Evoque", minYear: 2011, maxYear: 2027), VModel(name: "Discovery Sport", minYear: 2014, maxYear: 2027), VModel(name: "Range Rover Velar", minYear: 2017, maxYear: 2027)],
        "Fiat": [VModel(name: "500", minYear: 2011, maxYear: 2020), VModel(name: "500L", minYear: 2013, maxYear: 2021), VModel(name: "500X", minYear: 2015, maxYear: 2024), VModel(name: "124 Spider", minYear: 2016, maxYear: 2021)],
    ]
    static let family: [String: String] = [
        "Ford": "Ford",
        "Chevrolet": "GM",
        "GMC": "GM",
        "Buick": "GM",
        "Cadillac": "GM",
        "Pontiac": "GM",
        "Oldsmobile": "GM",
        "Saturn": "GM",
        "Hummer": "GM",
        "Lincoln": "Ford",
        "Mercury": "Ford",
        "Dodge": "Dodge",
        "Ram": "Ram",
        "Jeep": "Jeep",
        "Chrysler": "Chrysler",
        "Plymouth": "Plymouth",
        "Toyota": "Toyota",
        "Lexus": "Toyota",
        "Scion": "Toyota",
        "Honda": "Honda",
        "Acura": "Honda",
        "Nissan": "Nissan",
        "Infiniti": "Nissan",
        "Hyundai": "Hyundai",
        "Genesis": "Hyundai",
        "Kia": "Kia",
        "Mazda": "Mazda",
        "Subaru": "Subaru",
        "Mitsubishi": "Mitsubishi",
        "Suzuki": "Suzuki",
        "Isuzu": "GM",
        "Volkswagen": "Volkswagen",
        "Audi": "Volkswagen",
        "BMW": "BMW",
        "Mini": "BMW",
        "Mercedes-Benz": "Mercedes-Benz",
        "Volvo": "Volvo",
        "Saab": "GM",
        "Porsche": "Volkswagen",
        "Jaguar": "Jaguar",
        "Land Rover": "Land Rover",
        "Fiat": "Chrysler",
    ]
}

enum CodeDetail {
    static let causes: [String: String] = [
        "boost": "Boost leak (cracked intercooler hose or loose clamp), faulty wastegate or turbo, or a bad boost sensor.",
        "cat": "Worn-out catalytic converter, a failing downstream O2 sensor, or an exhaust leak. Fix any misfire or oil-burning problem first - those are what kill converters.",
        "crankcam": "Faulty sensor, damaged wiring or connector, or a damaged reluctor/tone ring.",
        "egr": "Carbon-clogged EGR passages or valve, or a faulty EGR valve/sensor.",
        "evap": "Loose, worn or wrong gas cap (check this first - it's free), cracked EVAP hoses, a faulty purge or vent valve, or a leaking charcoal canister. Shops find small leaks with a smoke test.",
        "fuelpressure": "Weak fuel pump, clogged fuel filter, faulty pressure regulator, or a bad fuel pressure sensor.",
        "idle": "Dirty throttle body (cleaning often fixes it), a vacuum leak, or a faulty idle control valve.",
        "lean": "Vacuum leak (cracked intake hose, PCV hose, intake gasket), dirty or failing MAF sensor, weak fuel pump or clogged fuel filter, or an exhaust leak ahead of the O2 sensor.",
        "maf": "Dirty MAF sensor (try MAF sensor cleaner), an air leak after the sensor, or a clogged air filter.",
        "misfire": "Worn spark plugs, a bad ignition coil, a clogged or leaking fuel injector, a vacuum leak, or low compression. Tip: swap that cylinder's coil with a neighbor - if the misfire follows the coil, the coil is bad. A flashing check-engine light means a severe misfire: avoid driving hard, it can overheat the catalytic converter.",
        "network": "Wiring or connector problem on the module network, a weak battery or low voltage, a blown fuse to the module that went silent, or a failed module.",
        "o2heater": "The O2 sensor's internal heater failed (replace the sensor), a blown fuse, or damaged wiring.",
        "postcat": "Exhaust leak, an upstream fuel-trim problem, or a failing O2 sensor.",
        "rich": "Leaking injector, fuel pressure too high, dirty MAF sensor, faulty coolant temperature sensor, or a clogged air filter.",
        "tcm": "The transmission computer has its own codes - they usually show up in this list too (look for 'Transmission'). Check those for the real fault.",
        "thermostat": "Thermostat stuck open (most common), low coolant, or a faulty coolant temperature sensor.",
        "timing": "Stretched timing chain or a belt that jumped a tooth, a faulty crank or cam sensor, or a VVT problem. Don't ignore this one - timing problems can damage the engine.",
        "voltage": "Weak battery, failing alternator, or corroded battery terminals / ground straps.",
        "vvt": "Low or dirty engine oil (check first), a faulty VVT/oil-control solenoid, or timing chain wear.",
        "wheelspeed": "Dirty or damaged wheel speed sensor, damaged wiring (common near the wheel), a rusty or cracked tone ring, or a worn wheel bearing on hubs with built-in sensors.",
    ]
    static let checks: [String: [String]] = [
        "boost": ["With the engine off, check the intercooler hoses and clamps for cracks or looseness.", "Look for oil or soot around hose joints, a sign of a boost leak.", "Have the turbo and wastegate checked if the hoses are fine."],
        "cat": ["Fix any misfire or fuel-trim codes first. They cause this code and ruin new converters.", "Check for exhaust leaks ahead of the rear oxygen sensor (black soot marks, ticking sound).", "In Live data, the rear oxygen sensor should stay fairly steady when warm. If it switches as fast as the front one, the converter is worn out."],
        "crankcam": ["Check the sensor's connector for corrosion or a loose fit, and the wiring for rubbing.", "Clear the code. If it comes back right away, the sensor is likely bad.", "On GM trucks, a crank relearn may be needed after replacing the crank sensor."],
        "dpfe": ["Find the DPFE sensor (small sensor with two rubber hoses going to the exhaust/EGR tube).", "Check both hoses for cracks, melting or being off. Make sure they aren't swapped.", "Replace the DPFE sensor if the hoses are fine. It's a common, inexpensive part on Fords."],
        "egr": ["Check the vacuum hoses and electrical connector at the EGR valve.", "Remove the EGR valve and look for heavy carbon. Clean the valve and passages.", "On Fords with a DPFE sensor (small sensor with two rubber hoses), check both hoses for cracks or being swapped. The sensor itself often fails and is inexpensive."],
        "evap": ["Check the gas cap: tighten until it clicks, and look at the rubber seal for cracks. A new cap is cheap and fixes many of these.", "Clear the code and drive for a few days. It can take several drives to re-test.", "If it comes back, look over the hoses near the charcoal canister and fuel tank for cracks.", "Small leaks are found fastest with a smoke test at a shop."],
        "fuelpressure": ["Listen for the fuel pump running for 2 seconds when you turn the key to ON.", "Replace the fuel filter if it's serviceable and overdue.", "Have the fuel pressure tested with a gauge to confirm a weak pump or bad regulator."],
        "gmtheft": ["Turn the key to ON and leave it for about 10 minutes until the security light stops flashing, then turn it off for 5 seconds and start (the GM relearn). If that doesn't work, do it three times (30 minutes).", "Check the battery is fully charged before trying.", "If it keeps happening, the ignition lock cylinder's sensor is often at fault."],
        "idle": ["Clean the throttle body with throttle-body cleaner (engine off, key out).", "Look for vacuum leaks around the intake.", "If it has an idle air control valve, check its connector and clean or replace it."],
        "lean": ["With the engine running, listen around the intake for a hiss (vacuum leak). Check the PCV hose and the big intake boot after the air filter for cracks.", "Check the air filter, and clean the airflow (MAF) sensor with MAF cleaner spray only.", "In Live data, watch the fuel trims: above +10% at idle that drops at 2,500 rpm points to a vacuum leak; high at both points to weak fuel delivery.", "If fuel delivery is suspect, have the fuel pressure tested."],
        "maf": ["Check the air filter and the intake boot between the sensor and the engine for cracks.", "Clean the airflow (MAF) sensor with MAF cleaner spray only. Let it dry before starting.", "If the code returns, check the connector, then replace the sensor."],
        "misfire": ["Look at Live data with the engine idling. Note which cylinder number the code names.", "Pull that cylinder's spark plug. Look for oil, heavy carbon, a cracked tip or a wide gap.", "Swap that cylinder's ignition coil with a neighbor's, clear the code and drive. If the misfire moves to the other cylinder, the coil is bad.", "If it stays, swap the spark plug the same way. If it still stays, have the injector and compression checked."],
        "network": ["Check the battery is charged and the terminals are tight. Low voltage causes many of these.", "Check the fuses for the module that stopped talking.", "Clear the codes and scan again. If the same module is missing, check its connector and power."],
        "o2heater": ["Check the fuse for the oxygen sensor heaters (see the owner's manual fuse chart).", "Look at the sensor wiring under the vehicle for melted or chafed spots near the exhaust.", "If the wiring and fuse are fine, replace the oxygen sensor the code names."],
        "pats": ["Try a different programmed key. A key with a damaged chip causes this.", "Keep other keys, fobs and metal keychains away from the ignition key.", "If you have two working keys you can add keys yourself (see the owner's manual). Otherwise a locksmith or the dealer can program one."],
        "postcat": ["Fix any front oxygen sensor or fuel-trim codes first.", "Check for exhaust leaks near the rear oxygen sensor.", "If those are fine, replace the rear oxygen sensor."],
        "rich": ["Check the air filter isn't clogged.", "Clean the airflow (MAF) sensor with MAF cleaner spray.", "In Live data, check the coolant temperature reads close to normal (about 190-220 °F) once warm. A sensor stuck cold makes the engine run rich.", "Have the fuel pressure checked for a regulator or leaking injector."],
        "thermostat": ["With the engine cold, check the coolant level.", "Drive 15 minutes and watch coolant temperature in Live data. If it stays below about 180 °F, the thermostat is likely stuck open.", "Replace the thermostat (and gasket). It's usually an inexpensive part."],
        "throttle": ["Clean the throttle body (engine off, key out).", "Check the throttle body and accelerator pedal connectors.", "If the code returns, the electronic throttle body usually needs replacing."],
        "timing": ["Don't keep driving hard: timing problems can damage the engine.", "Check the oil level and condition.", "Check the crank and cam sensor connectors and wiring.", "If those are fine, have the timing chain or belt checked for stretch or a jumped tooth."],
        "transmission": ["Check the transmission fluid level and smell (with the engine warm and running on most trucks). Burnt-smelling or dark fluid means wear.", "Look for other transmission codes in this list. They usually point to the real problem.", "Check the connector on the side of the transmission for corrosion.", "Slipping usually needs a transmission shop."],
        "voltage": ["Check the battery terminals and ground straps are clean and tight.", "Look at Battery on the Vehicle page with the engine off: under about 12.4 volts means a weak or discharged battery.", "With the engine running it should read about 13.5-14.7 volts. Lower points to the alternator.", "Most parts stores test the battery and alternator for free."],
        "vvt": ["Check the engine oil level and condition first. Low or dirty oil causes most of these.", "Change the oil and filter with the right grade if it's due.", "If the code returns, check the oil-control (VVT) solenoid's connector, then test or replace the solenoid."],
        "wheelspeed": ["Note which wheel the code names. Look at that wheel's sensor wire for damage near the hub.", "Unplug the sensor, check for corrosion, and plug it back in firmly.", "Remove the sensor and clean any rust or metal debris from its tip.", "With Live data on a test drive, a sensor that drops to 0 while the others read speed is bad. A worn wheel bearing with a built-in sensor can also cause it."],
    ]
    static let checkCodes: [String: [String]] = [
        "transmission": ["P0730", "P0731", "P0732", "P0733", "P0734", "P0741", "P0218"],
        "throttle": ["P2135", "P2101", "P2119", "P0121", "P0122", "P0123"],
    ]
    static let checkCodesByFamily: [String: [String: [String]]] = [
        "ford": [
            "pats": ["P1260"],
            "dpfe": ["P1400", "P1401", "P1405", "P1406"],
            "transmission": ["P1700", "P1728", "P1744", "P1783"],
            "lean": ["P1131", "P1151"],
            "rich": ["P1132", "P1152"],
            "maf": ["P1100", "P1101"],
            "egr": ["P1408", "P1409"],
            "idle": ["P1504", "P1505", "P1506", "P1507"],
            "voltage": ["B1318"],
            "wheelspeed": ["C1145", "C1155", "C1165", "C1175", "C1222", "C1233", "C1234", "C1235", "C1236"],
            "network": ["U1262", "U1900"],
        ],
        "gm": [
            "gmtheft": ["P1626", "P1630", "P1631"],
            "transmission": ["P1870"],
            "throttle": ["P1516", "P1125"],
            "maf": ["P1101"],
            "egr": ["P1406"],
            "idle": ["P1508", "P1509"],
            "voltage": ["C0896"],
            "network": ["U1000", "U1016", "U1041", "U1064", "U1088"],
            "crankcam": ["P1345"],
        ],
    ]
}

// Logic ported from the Mac app: which causes / check steps / urgency apply to a code.
extension CodeDetail {
    static func base(_ code: String) -> String { String(code.split(separator: "-").first ?? Substring(code)).uppercased() }

    /// Which group of usual causes a generic code belongs to ("" if none).
    static func causeKey(_ code: String) -> String {
        let c = base(code)
        func inSet(_ s: [String]) -> Bool { s.contains(c) }
        if "P0300"..."P0312" ~= c { return "misfire" }
        if inSet(["P0171","P0174","P0170","P0173","P2187","P2189"]) { return "lean" }
        if inSet(["P0172","P0175","P2188","P2190"]) { return "rich" }
        if inSet(["P0420","P0421","P0430","P0431"]) { return "cat" }
        if "P0440"..."P0457" ~= c { return "evap" }
        if inSet(["P0128","P0125"]) { return "thermostat" }
        if inSet(["P0010","P0011","P0012","P0013","P0014","P0015","P0020","P0021","P0022"]) { return "vvt" }
        if inSet(["P0016","P0017","P0018","P0019"]) { return "timing" }
        if "P0400"..."P0406" ~= c { return "egr" }
        if inSet(["P0505","P0506","P0507"]) { return "idle" }
        if ("P0030"..."P0058" ~= c) || inSet(["P0135","P0141","P0147","P0155","P0161","P0167"]) { return "o2heater" }
        if inSet(["P0560","P0562","P0563","P0620","P0621","P0622"]) { return "voltage" }
        if c == "P0700" { return "tcm" }
        if ("P0335"..."P0349" ~= c) || inSet(["P0365","P0366"]) { return "crankcam" }
        if "P0100"..."P0104" ~= c { return "maf" }
        if c.hasPrefix("U0") { return "network" }
        if inSet(["P0087","P0088","P0089","P0190","P0191","P0192","P0193"]) { return "fuelpressure" }
        if inSet(["P0234","P0299"]) { return "boost" }
        if inSet(["P2096","P2097","P2098","P2099"]) { return "postcat" }
        if inSet(["C0035","C0040","C0045","C0050"]) { return "wheelspeed" }
        return ""
    }

    static func commonCauses(_ code: String) -> String { causes[causeKey(code)] ?? "" }

    static func checkSteps(_ code: String, make: Make) -> [String] {
        let c = base(code)
        let fam = (make == .ford) ? "ford" : (make == .gm ? "gm" : "")
        if let famTable = checkCodesByFamily[fam] {
            for (key, codes) in famTable where codes.contains(c) { return checks[key] ?? [] }
        }
        for (key, codes) in checkCodes where codes.contains(c) { return checks[key] ?? [] }
        return checks[causeKey(code)] ?? []
    }

    private static func isEvap(_ c: String) -> Bool { "P0440"..."P0457" ~= c }

    static func severity(_ code: String, status: String, module: String) -> String {
        let c = base(code); let s = status.lowercased(); let m = module.lowercased()
        if s.contains("history") || s.contains("past") { return "past" }
        if s.contains("pending") || s.contains("permanent") { return "low" }
        if m.contains("airbag") || m.contains("restraint") || m.contains("abs") || m.contains("brake") { return "high" }
        if "P0300"..."P0312" ~= c || c == "P0217" || c == "P0524" { return "high" }
        if isEvap(c) { return "low" }
        return "medium"
    }

    static func whyItMatters(_ code: String, status: String, module: String) -> String {
        let c = base(code); let s = status.lowercased(); let m = module.lowercased()
        if s.contains("history") || s.contains("past") { return "This happened before but isn't happening right now. Often a loose connector or a wire that rubs." }
        if s.contains("permanent") { return "The vehicle is waiting to re-test this after a repair. It clears itself after a few normal drives once the problem is fixed." }
        if s.contains("pending") { return "The vehicle noticed this once. If it happens again on another drive, it becomes a stored code." }
        if m.contains("airbag") || m.contains("restraint") { return "The airbag light is probably on. Airbags may not deploy in a crash until this is fixed." }
        if m.contains("abs") || m.contains("brake") { return "ABS and traction control may be switched off. Your normal brakes still work, but the wheels can lock up in a hard stop." }
        if "P0300"..."P0312" ~= c { return "A misfire wastes fuel and can overheat and ruin the catalytic converter. If the check-engine light is flashing, avoid hard driving." }
        if c == "P0217" { return "The engine is overheating. Stop driving and let it cool to avoid serious engine damage." }
        if c == "P0524" { return "Low oil pressure can destroy the engine. Check the oil level before driving again." }
        if isEvap(c) { return "This affects emissions, not how the vehicle drives. It will fail an emissions test until fixed." }
        if c.hasPrefix("U") { return "Modules aren't talking to each other properly. That can cause odd warning lights or features that stop working." }
        return "This can affect how the vehicle runs or its emissions. Have it looked at when you can."
    }
}
