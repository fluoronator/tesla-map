#!/usr/bin/env python3
"""
Mister Car Wash Address Scraper
Uses Selenium to open each store page in Chrome, wait for JavaScript to load,
then scrape the street address. Saves results to mistercarwash_addresses.csv.

Requirements (run these in a command prompt first):
  pip install selenium webdriver-manager

Then just double-click this script to run it.
Takes about 15-20 minutes for all ~480 locations.
"""

import csv, time, os, sys, traceback

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                           "mistercarwash_addresses.csv")

# All stores from mistercarwash.com/store/
STORES = [
    # (display_name, city, state, slug)
    # AL
    ("Highway 280 CW",    "Birmingham",       "AL", "highway-280-cw"),
    ("Vestavia Wash",     "Vestavia Hills",   "AL", "vestavia-wash"),
    ("Oxford",            "Oxford",           "AL", "oxford"),
    ("Madison",           "Madison",          "AL", "madison"),
    ("Hartselle",         "Huntsville",       "AL", "hartselle"),
    ("Bassette Ave",      "Decatur",          "AL", "bassette-ave"),
    ("Limestone",         "Athens",           "AL", "limestone"),
    ("Setter",            "Decatur",          "AL", "setter"),
    ("9th Street",        "Decatur",          "AL", "9th-street"),
    ("Azalea",            "Florence",         "AL", "azalea"),
    ("Muscle Shoals",     "Muscle Shoals",    "AL", "muscle-shoals"),
    ("Cloverdale",        "Florence",         "AL", "cloverdale"),
    ("E. Madison",        "Huntsville",       "AL", "e-madison"),
    # AZ
    ("Tucson Mall",       "Tucson",           "AZ", "tucson-mall-2552"),
    ("Rillito",           "Tucson",           "AZ", "rillito-2552"),
    ("Twin Peaks",        "Tucson",           "AZ", "twin-peaks-1331"),
    ("Cardinal",          "Tucson",           "AZ", "cardinal"),
    ("Craycroft",         "Tucson",           "AZ", "craycroft"),
    ("Tangerine",         "Tucson",           "AZ", "tangerine"),
    ("Houghton",          "Tucson",           "AZ", "houghton"),
    ("Pandora Ave",       "Tucson",           "AZ", "pandora-ave"),
    ("Thornydale",        "Tucson",           "AZ", "thornydale"),
    ("Sierra Vista",      "Sierra Vista",     "AZ", "sierra-vista"),
    ("Sahuarita",         "Sahuarita",        "AZ", "sahuarita"),
    ("South Kolb",        "Tucson",           "AZ", "s-kolb"),
    ("E. 22nd",           "Tucson",           "AZ", "e-22nd"),
    ("Kino",              "Tucson",           "AZ", "kino"),
    ("Midvale",           "Tucson",           "AZ", "midvale"),
    ("Swan",              "Tucson",           "AZ", "swan"),
    ("Tanque Verde",      "Tucson",           "AZ", "tanque-verde"),
    ("Speedway",          "Tucson",           "AZ", "speedway"),
    ("Euclid",            "Tucson",           "AZ", "euclid"),
    ("E. Grant",          "Tucson",           "AZ", "e-grant"),
    ("Miracle Mile",      "Tucson",           "AZ", "miracle-mile"),
    ("North Oracle",      "Tucson",           "AZ", "north-oracle"),
    ("W. River",          "Tucson",           "AZ", "w-river"),
    ("Oro Valley",        "Tucson",           "AZ", "oro-valley"),
    ("Cortaro",           "Tucson",           "AZ", "cortaro"),
    # CA
    ("Ceres",             "Ceres",            "CA", "ceres-2564"),
    ("Carmen",            "Bakersfield",      "CA", "carmen-1034"),
    ("Reedley",           "Reedley",          "CA", "reedley-1072"),
    ("Tuolumne",          "Turlock",          "CA", "tuolumne-1076"),
    ("Hosking",           "Bakersfield",      "CA", "hosking-1035"),
    ("Bear Valley",       "Apple Valley",     "CA", "bear-valley-1064"),
    ("Jellico Ave",       "Hesperia",         "CA", "jellico-ave-1031"),
    ("Hwy 138",           "Palmdale",         "CA", "hwy-138"),
    ("Maybury St",        "Santa Ana",        "CA", "maybury-st"),
    ("Brookhurst St",     "Anaheim",          "CA", "brookhurst-st"),
    ("Varsity",           "San Bernardino",   "CA", "varsity"),
    ("Stoneridge",        "Moreno Valley",    "CA", "stoneridge"),
    ("Stockdale",         "Bakersfield",      "CA", "stockdale"),
    ("Inglewood Ave",     "Inglewood",        "CA", "inglewood-ave"),
    ("Montebello Blvd",   "Montebello",       "CA", "montbello-blvd"),
    ("Heath",             "Bakersfield",      "CA", "heath"),
    ("Happy Trails Hwy",  "Apple Valley",     "CA", "happy-trails-hwy"),
    ("Mooney Blvd",       "Visalia",          "CA", "mooney-blvd"),
    ("Marguerita Ave",    "Alhambra",         "CA", "marguerita-ave"),
    ("Rialto",            "Rialto",           "CA", "rialto"),
    ("Bear Creek",        "Merced",           "CA", "bear-creek"),
    ("Applegate Ranch",   "Atwater",          "CA", "applegate-ranch"),
    ("Industrial Blvd",   "Victorville",      "CA", "industrial-blvd"),
    ("Topaz",             "Victorville",      "CA", "topaz"),
    ("Ming Ave",          "Bakersfield",      "CA", "ming-ave"),
    ("McArt",             "Victorville",      "CA", "mcart"),
    ("Escondido Ave",     "Hesperia",         "CA", "escondido-ave"),
    ("G St",              "Merced",           "CA", "g-st"),
    ("Rosedale Hwy",      "Bakersfield",      "CA", "rosedale-hwy"),
    ("Lodi Wash",         "Lodi",             "CA", "lodi-wash"),
    ("Tracy",             "Tracy",            "CA", "tracy"),
    ("Manteca",           "Manteca",          "CA", "manteca"),
    ("Airport",           "Manteca",          "CA", "airport"),
    ("Dale Road",         "Modesto",          "CA", "dale-road"),
    ("Briggsmore",        "Modesto",          "CA", "briggsmore"),
    ("Patterson",         "Patterson",        "CA", "patterson"),
    ("North McHenry",     "Modesto",          "CA", "north-mchenry"),
    ("Riverbank",         "Riverbank",        "CA", "riverbank"),
    ("South McHenry",     "Modesto",          "CA", "south-mchenry"),
    ("Claribel",          "Riverbank",        "CA", "claribel"),
    ("Plaza",             "Modesto",          "CA", "plaza"),
    ("Hatch",             "Ceres",            "CA", "hatch"),
    ("Oakdale",           "Oakdale",          "CA", "oakdale"),
    ("Whitmore",          "Ceres",            "CA", "whitmore"),
    ("Monte Vista",       "Turlock",          "CA", "monte-vista"),
    ("Geer",              "Turlock",          "CA", "geer"),
    ("Los Banos",         "Los Banos",        "CA", "los-banos"),
    ("Atwater",           "Atwater",          "CA", "atwater"),
    ("Merced",            "Merced",           "CA", "merced"),
    ("Merced 16th",       "Merced",           "CA", "merced-16th"),
    ("Centennial Way",    "Hanford",          "CA", "centennial-way"),
    ("11th Ave",          "Hanford",          "CA", "11th-ave"),
    ("Dinuba",            "Dinuba",           "CA", "dinuba"),
    ("Tulare",            "Tulare",           "CA", "tulare"),
    ("Delano",            "Delano",           "CA", "delano"),
    ("Henderson Ave",     "Porterville",      "CA", "henderson-ave"),
    ("Jaye Street",       "Porterville",      "CA", "jaye-street"),
    ("Buena Vista",       "Bakersfield",      "CA", "buena-vista"),
    ("Calloway",          "Bakersfield",      "CA", "calloway"),
    ("Coffee",            "Bakersfield",      "CA", "coffee"),
    ("Olive",             "Bakersfield",      "CA", "olive"),
    ("Gosford",           "Bakersfield",      "CA", "gosford"),
    ("23rd Street",       "Bakersfield",      "CA", "23rd-street"),
    ("Panama",            "Bakersfield",      "CA", "panama"),
    ("Mount Vernon",      "Bakersfield",      "CA", "mount-vernon"),
    ("Avenue J",          "Lancaster",        "CA", "avenue-j"),
    ("Palmdale",          "Palmdale",         "CA", "palmdale"),
    ("Geer Wash",         "Turlock",          "CA", "geer-wash"),
    # CO
    ("Runway North",      "Denver",           "CO", "runway-north"),
    ("Monument",          "Monument",         "CO", "monument"),
    ("Constitution",      "Colorado Springs", "CO", "constitution"),
    ("Academy Blvd",      "Colorado Springs", "CO", "academy-blvd"),
    ("Old Ranch Rd",      "Colorado Springs", "CO", "old-ranch-rd"),
    ("Prospect Ave",      "Aurora",           "CO", "prospect-ave-2"),
    ("Woodmen",           "Colorado Springs", "CO", "woodmen"),
    ("Bradley",           "Colorado Springs", "CO", "bradley"),
    ("Fountain",          "Fountain",         "CO", "fountain"),
    ("Pueblo",            "Pueblo",           "CO", "pueblo"),
    ("Glenroyal",         "Pueblo",           "CO", "glenroyal"),
    # FL
    ("Zephyrhills",       "Zephyrhills",      "FL", "zephyrhills-2501"),
    ("Goldenrod",         "Jensen Beach",     "FL", "goldenrod"),
    ("Belvedere",         "The Villages",     "FL", "belvedere"),
    ("NE 16th Place",     "Cape Coral",       "FL", "ne-16th-place"),
    ("Park Ridge",        "Pinellas Park",    "FL", "park-ridge"),
    ("Millenia",          "Orlando",          "FL", "millenia"),
    ("Long Key",          "Wildwood",         "FL", "long-key"),
    ("Irwin",             "Melbourne",        "FL", "irwin"),
    ("Mulberry",          "Mulberry",         "FL", "mulberry"),
    ("Liberty Park",      "Cape Coral",       "FL", "liberty-park"),
    ("Oaks Blvd",         "Kissimmee",        "FL", "oaks-blvd"),
    ("Winter Haven",      "Winter Haven",     "FL", "winter-haven"),
    ("Altamonte",         "Altamonte Springs","FL", "altamonte"),
    ("Oviedo",            "Oviedo",           "FL", "oviedo"),
    ("Old Cheney Hwy",    "Orlando",          "FL", "old-cheney-hwy"),
    ("Poinciana",         "Poinciana",        "FL", "poinciana"),
    ("Hwy 50",            "Clermont",         "FL", "hwy-50"),
    ("Landstar",          "Orlando",          "FL", "landstar"),
    ("Lake Nona",         "Orlando",          "FL", "lake-nona"),
    ("Curry Ford",        "Orlando",          "FL", "curry-ford"),
    ("Semoran",           "Orlando",          "FL", "semoran"),
    ("Red Bug",           "Oviedo",           "FL", "red-bug"),
    ("Clyde Morris Blvd", "Port Orange",      "FL", "clyde-morris-blvd"),
    ("Sanford Wash",      "Sanford",          "FL", "sanford-wash"),
    ("Lake Mary Wash",    "Lake Mary",        "FL", "lake-mary-wash"),
    ("Melbourne Wash",    "Melbourne",        "FL", "melbourne-wash"),
    ("Airport Pulling Rd","Naples",           "FL", "airport-pulling-rd"),
    ("Bonita",            "Bonita Springs",   "FL", "bonita"),
    ("Cody Lee",          "Fort Myers",       "FL", "cody-lee"),
    ("Rattlesnake",       "Naples",           "FL", "rattlesnake"),
    ("Arborwood",         "Fort Myers",       "FL", "arborwood"),
    ("Metro Pkwy",        "Fort Myers",       "FL", "metro-pkwy"),
    ("McCall",            "Port Charlotte",   "FL", "mccall"),
    ("Estero",            "Estero",           "FL", "estero"),
    ("S Federal Hwy",     "Port St. Lucie",   "FL", "s-federal-hwy"),
    ("Port St. Lucie",    "Port Saint Lucie", "FL", "port-st-lucie"),
    ("Cutler Bay",        "Miami",            "FL", "cutler-bay"),
    ("Hypoluxo",          "Lantana",          "FL", "hypoluxo"),
    ("Hillsborough",      "Tampa",            "FL", "hillsborough"),
    ("Wesley Chapel",     "Wesley Chapel",    "FL", "wesley-chapel"),
    ("Land O Lakes",      "Lutz",             "FL", "land-o-lakes"),
    ("Bruce B Downs",     "Tampa",            "FL", "bruce-b-downs"),
    ("Florida Ave S",     "Lakeland",         "FL", "florida-ave-s"),
    ("Hwy 98 N",          "Lakeland",         "FL", "hwy-98-n"),
    ("Havendale Blvd",    "Winter Haven",     "FL", "havendale-blvd"),
    ("Bartow Road",       "Lakeland",         "FL", "bartow-road"),
    ("Viera",             "Rockledge",        "FL", "viera"),
    ("Titusville",        "Titusville",       "FL", "titusville"),
    ("Cape Coral Pkwy",   "Cape Coral",       "FL", "cape-coral-pkwy"),
    ("Del Prado",         "Cape Coral",       "FL", "del-prado"),
    ("Santa Barbara Blvd","Cape Coral",       "FL", "santa-barbara-blvd"),
    ("Skyline Blvd",      "Cape Coral",       "FL", "skyline-blvd"),
    ("Pine Island",       "Cape Coral",       "FL", "pine-island"),
    ("Irlo Bronson",      "St. Cloud",        "FL", "irlo-bronson"),
    ("Neptune",           "Saint Cloud",      "FL", "neptune"),
    ("Commerce Ctr Dr",   "Saint Cloud",      "FL", "commerce-ctr-dr"),
    ("Colonial",          "Orlando",          "FL", "colonial"),
    ("Chickasaw",         "Orlando",          "FL", "chickasaw"),
    ("Port Orange",       "Port Orange",      "FL", "port-orange"),
    ("Kissimmee",         "Kissimmee",        "FL", "kissimmee"),
    ("Cypress Gardens",   "Winter Haven",     "FL", "cypress-gardens"),
    ("Orange Blossom",    "Orlando",          "FL", "orange-blossom"),
    ("French Ave",        "Sanford",          "FL", "french-ave"),
    ("Fern Park",         "Casselberry",      "FL", "fern-park"),
    ("LPGA",              "Daytona Beach",    "FL", "lpga"),
    ("Ormond Beach",      "Ormond Beach",     "FL", "ormond-beach"),
    ("Lee Rd",            "Orlando",          "FL", "lee-rd"),
    ("Deltona",           "Deltona",          "FL", "deltona"),
    ("Silver Star",       "Orlando",          "FL", "silver-star"),
    ("Sanford",           "Sanford",          "FL", "sanford"),
    ("Ocoee",             "Ocoee",            "FL", "ocoee"),
    ("Miriam",            "Lakeland",         "FL", "miriam"),
    ("Palm Coast",        "Palm Coast",       "FL", "palm-coast"),
    ("Highway 27",        "Clermont",         "FL", "highway-27"),
    ("Clermont",          "Clermont",         "FL", "clermont"),
    ("Mt. Dora",          "Mount Dora",       "FL", "mt-dora"),
    ("Tavares",           "Tavares",          "FL", "tavares"),
    ("Leesburg",          "Leesburg",         "FL", "leesburg"),
    ("Brandon",           "Brandon",          "FL", "brandon"),
    ("Adamo",             "Brandon",          "FL", "adamo"),
    ("Gandy",             "Tampa",            "FL", "gandy"),
    ("Dale Mabry",        "Tampa",            "FL", "dale-mabry"),
    ("North Dale Mabry",  "Tampa",            "FL", "north-dale-mabry"),
    ("Seminole",          "Seminole",         "FL", "seminole"),
    ("Clearwater",        "Clearwater",       "FL", "clearwater"),
    ("State Route 52",    "Hudson",           "FL", "state-route-52"),
    ("Spring Hill",       "Spring Hill",      "FL", "spring-hill"),
    ("Hudson",            "Hudson",           "FL", "hudson"),
    # GA
    ("Pleasant Hill Rd",  "Duluth",           "GA", "pleasant-hill-rd"),
    ("Ponce De Leon",     "Atlanta",          "GA", "ponce-de-leon"),
    ("Athens",            "Athens",           "GA", "athens"),
    ("Monroe",            "Monroe",           "GA", "monroe"),
    ("Covington",         "Covington",        "GA", "covington"),
    ("Conyers",           "Conyers",          "GA", "conyers"),
    ("Dawsonville Hwy",   "Gainesville",      "GA", "dawsonville-hwy"),
    ("Buford",            "Buford",           "GA", "buford"),
    ("Stone Mountain",    "Lilburn",          "GA", "stone-mountain"),
    ("Griffin",           "Griffin",          "GA", "griffin"),
    ("Cumming",           "Cumming",          "GA", "cumming"),
    ("Lovejoy",           "Hampton",          "GA", "lovejoy"),
    ("Peachtree",         "Cumming",          "GA", "peachtree"),
    ("State Bridge",      "Alpharetta",       "GA", "state-bridge"),
    ("Piedmont",          "Atlanta",          "GA", "piedmont"),
    ("Old National",      "College Park",     "GA", "old-national"),
    ("Riverstone",        "Canton",           "GA", "riverstone"),
    ("Marietta",          "Marietta",         "GA", "marietta"),
    ("Douglasville",      "Douglasville",     "GA", "douglasville"),
    ("Hiram",             "Hiram",            "GA", "hiram"),
    ("Acworth",           "Acworth",          "GA", "acworth"),
    ("Aspen Drive",       "Dallas",           "GA", "aspen-drive"),
    ("Grace",             "Athens",           "GA", "grace"),
    # IA
    ("Kimberly Rd",       "Davenport",        "IA", "kimberly-rd"),
    ("Hickman",           "Waukee",           "IA", "hickman"),
    ("Lakeview",          "Davenport",        "IA", "lakeview"),
    ("Altoona",           "Altoona",          "IA", "altoona"),
    ("12th Ave",          "Pleasant Hill",    "IA", "12th-ave"),
    ("North Merle Hay",   "Urbandale",        "IA", "north-merle-hay"),
    ("Marion",            "Marion",           "IA", "marion"),
    ("Northland",         "Cedar Rapids",     "IA", "northland"),
    ("Blairs Ferry",      "Cedar Rapids",     "IA", "blairs-ferry"),
    ("Williams Blvd",     "Cedar Rapids",     "IA", "williams-blvd"),
    ("Ankeny",            "Ankeny",           "IA", "ankeny"),
    ("14th Street",       "Des Moines",       "IA", "14th-street"),
    ("Ingersoll",         "Des Moines",       "IA", "ingersoll"),
    ("Army Post",         "Des Moines",       "IA", "army-post"),
    ("Merle Hay",         "Des Moines",       "IA", "merle-hay"),
    ("Grimes",            "Grimes",           "IA", "grimes"),
    ("University",        "Clive",            "IA", "university"),
    ("Urbandale",         "Urbandale",        "IA", "urbandale"),
    ("Jordan Creek",      "West Des Moines",  "IA", "jordan-creek"),
    # ID
    ("Progress Ave",      "Meridian",         "ID", "progress-ave"),
    ("Milano",            "Meridian",         "ID", "milano"),
    ("Nampa",             "Nampa",            "ID", "nampa"),
    ("Garrity",           "Nampa",            "ID", "garrity"),
    ("Meridian",          "Meridian",         "ID", "meridian"),
    ("Fairview",          "Boise",            "ID", "fairview"),
    ("Front Street",      "Boise",            "ID", "front-street"),
    ("Broadway",          "Boise",            "ID", "broadway"),
    # IL
    ("Loves Park",        "Loves Park",       "IL", "loves-park"),
    ("Kimber",            "Machesney Park",   "IL", "kimber"),
    ("State St",          "Rockford",         "IL", "state-st"),
    # MD
    ("Annapolis",         "Edgewater",        "MD", "annapolis"),
    ("Severna",           "Millersville",     "MD", "severna"),
    # MI
    ("Waterford",         "Waterford Twp",    "MI", "waterford-2554"),
    ("Mount Clemens",     "Mount Clemens",    "MI", "mount-clemens-2567"),
    ("New Baltimore",     "New Baltimore",    "MI", "new-baltimore-2537"),
    ("Clarkston",         "Grand Rapids",     "MI", "clarkston-2538"),
    ("Argyle",            "Jackson",          "MI", "argyle-2570"),
    ("Latson",            "Howell",           "MI", "latson-1495"),
    ("Frenchtown",        "Monroe",           "MI", "frenchtown"),
    ("Ford Rd",           "Canton",           "MI", "ford-rd"),
    ("Holland",           "Holland",          "MI", "holland"),
    ("Leonard",           "Grand Rapids",     "MI", "leonard"),
    ("Fuller Street",     "Grand Rapids",     "MI", "fuller-street"),
    ("28th Street",       "Grand Rapids",     "MI", "28th-street"),
    ("Center Ave",        "Essexville",       "MI", "center-ave"),
    ("Wilder",            "Bay City",         "MI", "wilder"),
    ("N. Union",          "Bay City",         "MI", "n-union"),
    ("Bay Road",          "Saginaw",          "MI", "bay-road"),
    ("Lawndale",          "Saginaw",          "MI", "lawndale"),
    ("Cinema",            "Midland",          "MI", "cinema"),
    ("Pickard",           "Mount Pleasant",   "MI", "pickard"),
    ("Craig Hill",        "Mount Pleasant",   "MI", "craig-hill"),
    ("Lansing",           "Lansing",          "MI", "lansing"),
    ("Grand Ledge",       "Grand Ledge",      "MI", "grand-ledge"),
    ("Greenville",        "Greenville",       "MI", "greenville"),
    ("Cascade",           "Grand Rapids",     "MI", "cascade"),
    ("10 Mile",           "Rockford",         "MI", "10-mile"),
    ("Beltline",          "Grand Rapids",     "MI", "beltline"),
    ("Plainfield",        "Grand Rapids",     "MI", "plainfield"),
    ("Woodland",          "Grand Rapids",     "MI", "woodland"),
    ("Junior",            "Grand Rapids",     "MI", "junior"),
    ("Kalamazoo",         "Grand Rapids",     "MI", "kalamazoo"),
    ("44th Street",       "Grand Rapids",     "MI", "44th-street"),
    ("Alpine",            "Comstock Park",    "MI", "alpine"),
    ("Wyoming",           "Wyoming",          "MI", "wyoming"),
    ("Byron Center",      "Byron Center",     "MI", "byron-center"),
    ("Walker",            "Grand Rapids",     "MI", "walker"),
    ("Jenison",           "Jenison",          "MI", "jenison"),
    # MN
    ("Stillwater",        "Stillwater",       "MN", "stillwater"),
    ("Arden Hills",       "Arden Hills",      "MN", "arden-hills"),
    ("Maplewood",         "Maplewood",        "MN", "maplewood"),
    ("Forest Lake",       "Forest Lake",      "MN", "forest-lake"),
    ("Flying Cloud",      "Eden Prairie",     "MN", "flying-cloud"),
    ("Springbrook",       "Coon Rapids",      "MN", "springbrook"),
    ("Duluth Heights",    "Duluth",           "MN", "duluth-heights"),
    ("Voyageur",          "Saint Cloud",      "MN", "voyageur"),
    ("Ulysses",           "Blaine",           "MN", "ulysses"),
    ("Mankato",           "Mankato",          "MN", "mankato"),
    ("Minnetonka",        "Minnetonka",       "MN", "minnetonka"),
    ("Fridley",           "Fridley",          "MN", "fridley"),
    ("Jefferson Hwy",     "Champlin",         "MN", "jefferson-hwy"),
    ("Round Lake Blvd",   "Anoka",            "MN", "round-lake-blvd"),
    ("Riverside",         "Saint Cloud",      "MN", "riverside"),
    ("Saint Cloud",       "Saint Cloud",      "MN", "saint-cloud"),
    ("Rogers",            "Rogers",           "MN", "rogers"),
    ("Shoreview",         "Shoreview",        "MN", "shoreview"),
    ("Cottage Grove",     "Cottage Grove",    "MN", "cottage-grove"),
    ("Downtowner",        "Saint Paul",       "MN", "downtowner"),
    ("Roseville",         "Roseville",        "MN", "roseville"),
    ("West St. Paul",     "West Saint Paul",  "MN", "west-st-paul"),
    ("Anoka",             "Anoka",            "MN", "anoka"),
    ("Columbia Heights",  "Columbia Heights", "MN", "columbia-heights"),
    ("Zane",              "Brooklyn Park",    "MN", "zane"),
    ("River Road",        "Rochester",        "MN", "river-road"),
    ("Brooklyn Park",     "Brooklyn Park",    "MN", "brooklyn-park"),
    ("71st Street",       "Brooklyn Park",    "MN", "71st-street"),
    ("41st Street",       "Rochester",        "MN", "41st-street"),
    ("Crossroads",        "Rochester",        "MN", "crossroads"),
    ("Plymouth",          "Plymouth",         "MN", "plymouth"),
    ("Apple Valley",      "Apple Valley",     "MN", "apple-valley"),
    ("St. Louis Park",    "Saint Louis Park", "MN", "st-louis-park"),
    ("Edina",             "Edina",            "MN", "edina"),
    ("St. Cloud",         "St Cloud",         "MN", "st-cloud"),
    # MO
    ("Republic",          "Republic",         "MO", "republic"),
    ("Route 66",          "Springfield",      "MO", "rte-66"),
    ("Mill St",           "Springfield",      "MO", "mill-st"),
    ("Sunshine",          "Springfield",      "MO", "sunshine"),
    ("Glenstone",         "Springfield",      "MO", "glenstone"),
    ("Battlefield",       "Springfield",      "MO", "battlefield"),
    ("Campbell",          "Springfield",      "MO", "campbell"),
    ("Kansas Expressway", "Springfield",      "MO", "kansas-expressway"),
    ("S. Cox",            "Springfield",      "MO", "s-cox"),
    # MS
    ("Stribling Lane",    "Brandon",          "MS", "stribling-lane"),
    ("Lakeland",          "Flowood",          "MS", "lakeland"),
    ("Richland",          "Richland",         "MS", "richland"),
    ("I-55",              "Jackson",          "MS", "i-55"),
    ("Ridgeland",         "Ridgeland",        "MS", "ridgeland"),
    ("Meadowbrook",       "Meadowbrook",      "MS", "meadowbrook"),
    ("Clinton",           "Clinton",          "MS", "clinton"),
    ("Hwy 39",            "Meridian",         "MS", "hwy-39"),
    # NM
    ("Fiesta Park",       "Albuquerque",      "NM", "fiesta-park"),
    ("Montoya",           "Rio Rancho",       "NM", "montoya"),
    ("Rio Bravo",         "Albuquerque",      "NM", "rio-bravo"),
    ("Sonoma Ranch",      "Las Cruces",       "NM", "sonoma-ranch"),
    ("Gibson",            "Albuquerque",      "NM", "gibson"),
    ("Los Lunas",         "Los Lunas",        "NM", "los-lunas"),
    ("Southern",          "Rio Rancho",       "NM", "southern"),
    ("Bernalillo",        "Bernalillo",       "NM", "bernalillo"),
    ("Snow Heights",      "Albuquerque",      "NM", "snow-heights"),
    ("San Pedro",         "Albuquerque",      "NM", "san-pedro"),
    ("San Mateo",         "Albuquerque",      "NM", "san-mateo"),
    ("Homestead",         "Albuquerque",      "NM", "homestead"),
    ("Valencia",          "Albuquerque",      "NM", "valencia"),
    ("Central Ave",       "Albuquerque",      "NM", "central-ave"),
    ("Highway 528",       "Albuquerque",      "NM", "highway-528"),
    ("Rio Rancho",        "Rio Rancho",       "NM", "rio-rancho"),
    ("2nd Street",        "Albuquerque",      "NM", "2nd-street"),
    ("Pinon Hills",       "Farmington",       "NM", "pinon-hills"),
    ("Coors Blvd",        "Albuquerque",      "NM", "coors-blvd"),
    ("E. 20th",           "Farmington",       "NM", "e-20th"),
    ("Volcano",           "Albuquerque",      "NM", "volcano"),
    ("West Main",         "Farmington",       "NM", "west-main"),
    ("Lujan",             "Las Cruces",       "NM", "lujan"),
    ("Rinconada",         "Las Cruces",       "NM", "rinconada"),
    ("Main St.",          "Las Cruces",       "NM", "main-st"),
    # PA
    ("Jonestown",         "Harrisburg",       "PA", "jonestown"),
    ("Lincoln Hwy",       "Lancaster",        "PA", "lincoln-hwy"),
    ("Reading",           "Reading",          "PA", "reading"),
    ("Ephrata",           "Ephrata",          "PA", "ephrata"),
    ("Lancaster",         "Lancaster",        "PA", "lancaster"),
    ("York",              "York",             "PA", "york"),
    # TN
    ("Carver Lane",       "Lebanon",          "TN", "carver-lane-847"),
    ("Columbia",          "Columbia",         "TN", "columbia"),
    ("Highway 96",        "Murfreesboro",     "TN", "highway-96"),
    ("Murfreesboro",      "Murfreesboro",     "TN", "murfreesboro"),
    ("Hwy 96",            "Murfreesboro",     "TN", "hwy-96"),
    ("Mount Juliet",      "Mount Juliet",     "TN", "mount-juliet"),
    ("Smyrna",            "Smyrna",           "TN", "smyrna"),
    ("Gallatin",          "Gallatin",         "TN", "gallatin"),
    ("LaVergne",          "Antioch",          "TN", "lavergne"),
    ("Hermitage",         "Hermitage",        "TN", "hermitage"),
    ("Hendersonville",    "Hendersonville",   "TN", "hendersonville"),
    ("Nashboro",          "Nashville",        "TN", "nashboro"),
    ("Northside",         "Madison",          "TN", "northside"),
    ("Nolensville Pike",  "Nashville",        "TN", "nolensville-pike"),
    ("East Nashville",    "Nashville",        "TN", "east-nashville"),
    ("Needmore",          "Clarksville",      "TN", "needmore"),
    ("Dunbar Cave",       "Clarksville",      "TN", "dunbar-cave"),
    ("Dover Crossing",    "Clarksville",      "TN", "dover-crossing"),
    # TX
    ("Justice",           "El Paso",          "TX", "justice-2546"),
    ("74th St",           "Lubbock",          "TX", "74th-st-2645"),
    ("Loop 289",          "Lubbock",          "TX", "loop-289-2644"),
    ("Slide Rd",          "Lubbock",          "TX", "slide-rd-2643"),
    ("Mac Davis",         "Lubbock",          "TX", "mac-davis-2641"),
    ("Pearland",          "Pearland",         "TX", "pearland-1114"),
    ("Perry Road",        "Houston",          "TX", "perry-road"),
    ("Kingwood",          "Humble",           "TX", "kingwood"),
    ("Fry",               "Cypress",          "TX", "fry"),
    ("Magnolia",          "Magnolia",         "TX", "magnolia"),
    ("Turner",            "El Paso",          "TX", "turner"),
    ("Nuevo Hueco",       "El Paso",          "TX", "nuevo-hueco"),
    ("Quail Valley",      "Abilene",          "TX", "quail-valley"),
    ("Greenmoor Dr",      "Magnolia",         "TX", "greenmoor-dr"),
    ("Sandstone Ranch",   "El Paso",          "TX", "sandstone-ranch"),
    ("Talbot",            "El Paso",          "TX", "talbot"),
    ("Joe Battle",        "El Paso",          "TX", "joe-battle"),
    ("Barker Cypress",    "Houston",          "TX", "barker-cypress"),
    ("Bellfort",          "Houston",          "TX", "bellfort"),
    ("Horizon Blvd",      "Horizon City",     "TX", "horizon-blvd"),
    ("Boudreaux Rd",      "Spring",           "TX", "boudreaux-rd"),
    ("Eastlake",          "El Paso",          "TX", "eastlake"),
    ("Pellicano",         "El Paso",          "TX", "pellicano"),
    ("Valley Ranch",      "New Caney",        "TX", "valley-ranch"),
    ("Sun Bowl Dr",       "El Paso",          "TX", "sun-bowl-dr"),
    ("Memorial Dr",       "Houston",          "TX", "memorial-dr"),
    ("Mason Road",        "Katy",             "TX", "mason-road"),
    ("Highway 6 North",   "Houston",          "TX", "highway-6-north"),
    ("Washington Ave",    "Houston",          "TX", "washington-ave"),
    ("Mesquite Wash",     "Mesquite",         "TX", "mesquite-wash"),
    ("Rankin Road",       "Houston",          "TX", "rankin-road"),
    ("Hwy 314",           "Abilene",          "TX", "hwy-314"),
    ("Kemah",             "Kemah",            "TX", "kemah"),
    ("Genesis",           "Webster",          "TX", "genesis"),
    ("Laurynnbrook",      "Pasadena",         "TX", "laurynnbrook"),
    ("Fairmont",          "Pasadena",         "TX", "fairmont"),
    ("Bliss Meadows",     "Pasadena",         "TX", "bliss-meadows"),
    ("Wallisville",       "Houston",          "TX", "wallisville"),
    ("Uvalde",            "Houston",          "TX", "uvalde"),
    ("Atascocita",        "Humble",           "TX", "atascocita"),
    ("Holcombe",          "Houston",          "TX", "holcombe"),
    ("South Main",        "Houston",          "TX", "south-main"),
    ("Humble",            "Humble",           "TX", "humble"),
    ("Upper Kirby",       "Houston",          "TX", "upper-kirby"),
    ("Kirby",             "Houston",          "TX", "kirby"),
    ("Crosstimbers",      "Houston",          "TX", "crosstimbers"),
    ("Galleria",          "Houston",          "TX", "galleria"),
    ("Hillcroft",         "Houston",          "TX", "hillcroft"),
    ("Highway 6",         "Missouri City",    "TX", "highway-6"),
    ("Voss",              "Houston",          "TX", "voss"),
    ("Bellaire",          "Houston",          "TX", "bellaire"),
    ("Dulles",            "Stafford",         "TX", "dulles"),
    ("Sugarland",         "Sugar Land",       "TX", "sugarland"),
    ("1960 East",         "Houston",          "TX", "1960-east"),
    ("Westheimer",        "Houston",          "TX", "westheimer"),
    ("Gessner",           "Houston",          "TX", "gessner"),
    ("Brigade",           "Houston",          "TX", "brigade"),
    ("Holzwarth",         "Spring",           "TX", "holzwarth"),
    ("Addicks-Howell",    "Houston",          "TX", "addicks-howell"),
    ("Champions",         "Houston",          "TX", "champions"),
    ("Louetta",           "Spring",           "TX", "louetta"),
    ("Copperfield",       "Houston",          "TX", "copperfield"),
    ("South Mason",       "Katy",             "TX", "south-mason"),
    ("Spring Green",      "Katy",             "TX", "spring-green"),
    ("Mesquite",          "Mesquite",         "TX", "mesquite"),
    ("Temple",            "Temple",           "TX", "temple"),
    ("Pflugerville",      "Pflugerville",     "TX", "pflugerville"),
    ("Gattis",            "Round Rock",       "TX", "gattis"),
    ("Research",          "Austin",           "TX", "research"),
    ("Burnet",            "Austin",           "TX", "burnet"),
    ("Round Rock",        "Round Rock",       "TX", "round-rock"),
    ("Oakwood Blvd",      "Round Rock",       "TX", "oakwood-blvd"),
    ("Whitestone",        "Cedar Park",       "TX", "whitestone"),
    ("MLK",               "Killeen",          "TX", "mlk"),
    ("Stan Schlueter Loop","Killeen",          "TX", "stan-schlueter-loop"),
    ("Ft. Cavazos",       "Fort Cavazos",     "TX", "ft-cavazos"),
    ("Hwy 190",           "Copperas Cove",    "TX", "hwy-190"),
    ("Judge Ely",         "Abilene",          "TX", "judge-ely"),
    ("S 27th",            "Abilene",          "TX", "s-27th"),
    ("Buffalo Gap",       "Abilene",          "TX", "buffalo-gap"),
    ("Pioneer",           "Abilene",          "TX", "pioneer"),
    ("Indiana Ave",       "Lubbock",          "TX", "indiana-ave"),
    ("Quaker",            "Lubbock",          "TX", "quaker"),
    ("4th Street",        "Lubbock",          "TX", "4th-street"),
    ("82nd Street",       "Lubbock",          "TX", "82nd-street"),
    ("Zaragoza",          "El Paso",          "TX", "zaragoza"),
    ("Vista Del Sol",     "El Paso",          "TX", "vista-del-sol"),
    ("Montwood",          "El Paso",          "TX", "montwood"),
    ("North Loop",        "El Paso",          "TX", "north-loop"),
    ("George Dieter",     "El Paso",          "TX", "george-dieter"),
    ("Alameda",           "El Paso",          "TX", "alameda"),
    ("Cielo Vista",       "El Paso",          "TX", "cielo-vista"),
    ("Montana",           "El Paso",          "TX", "montana"),
    ("Dyer",              "El Paso",          "TX", "dyer"),
    ("Hondo Pass",        "El Paso",          "TX", "hondo-pass"),
    ("Coronado",          "El Paso",          "TX", "coronado"),
    ("Sunland Park",      "El Paso",          "TX", "sunland-park"),
    ("Desert Trail",      "El Paso",          "TX", "desert-trail"),
    ("Osborne",           "El Paso",          "TX", "osborne"),
    ("Paseo Del Norte",   "El Paso",          "TX", "paseo-del-norte"),
    # UT
    ("Syracuse",          "Syracuse",         "UT", "syracuse"),
    ("Hwy 89",            "Salt Lake City",   "UT", "hwy-89"),
    ("Cherry Hill",       "Orem",             "UT", "cherry-hill"),
    ("Kaysville",         "Kaysville",        "UT", "kaysville"),
    ("Vineyard",          "Orem",             "UT", "vineyard"),
    ("Redwood",           "Taylorsville",     "UT", "redwood"),
    ("South Salt Lake",   "Salt Lake City",   "UT", "south-salt-lake"),
    ("Foothills",         "Salt Lake City",   "UT", "foothills"),
    ("Washington-2",      "Ogden",            "UT", "washington-2"),
    ("Layton",            "Layton",           "UT", "layton"),
    ("Bountiful",         "Bountiful",        "UT", "bountiful"),
    ("Park City",         "Park City",        "UT", "park-city"),
    ("Millcreek",         "Salt Lake City",   "UT", "millcreek"),
    ("West Valley",       "West Valley City", "UT", "west-valley"),
    ("Taylorsville",      "Salt Lake City",   "UT", "taylorsville"),
    ("Cottonwood",        "Cottonwood Heights","UT","cottonwood"),
    ("Highlands",         "West Jordan",      "UT", "highlands"),
    ("West Jordan",       "West Jordan",      "UT", "west-jordan"),
    ("Sandy",             "Sandy",            "UT", "sandy"),
    ("South Jordan",      "South Jordan",     "UT", "south-jordan"),
    ("Anthem",            "Herriman",         "UT", "anthem"),
    ("Draper",            "Draper",           "UT", "draper"),
    ("Riverton",          "Riverton",         "UT", "riverton"),
    ("American Fork",     "American Fork",    "UT", "american-fork"),
    # WA
    ("Greenstone",        "Spokane",          "WA", "greenstone-2545"),
    ("McClellan",         "Spokane",          "WA", "mcclellan-1581"),
    ("Regal",             "Spokane",          "WA", "regal"),
    ("Hoerner St",        "Spokane",          "WA", "hoerner-st"),
    ("Five Mile",         "Spokane",          "WA", "five-mile"),
    ("N. Division",       "Spokane",          "WA", "n-division"),
    ("Sunset Hwy",        "Spokane",          "WA", "sunset-hwy"),
    ("N. Pines",          "Spokane",          "WA", "n-pines"),
    ("N. Sullivan",       "Spokane",          "WA", "n-sullivan"),
    ("Moses Lake",        "Moses Lake",       "WA", "moses-lake"),
    ("Kennedy Rd.",       "West Richland",    "WA", "kennedy-rd"),
    ("Aaron Dr",          "Richland",         "WA", "aaron-dr"),
    ("Burden Blvd",       "Pasco",            "WA", "burden-blvd"),
    ("West Court St",     "Pasco",            "WA", "west-court-st"),
    ("Kennewick",         "Kennewick",        "WA", "kennewick"),
    ("Okanogan Pl",       "Kennewick",        "WA", "okanogan-pl"),
    ("Fruitland",         "Kennewick",        "WA", "fruitland"),
    ("9th Ave",           "Walla Walla",      "WA", "9th-ave"),
    # WI
    ("Onalaska",          "La Crosse",        "WI", "onalaska"),
    ("Kenosha",           "Kenosha",          "WI", "kenosha"),
    ("Market Lane",       "Kenosha",          "WI", "market-lane"),
    ("Castle Manor",      "Greenfield",       "WI", "castle-manor"),
    ("Badger",            "Hudson",           "WI", "badger-dr"),
    ("University Ave",    "Madison",          "WI", "university-ave"),
    ("Cudahy",            "Cudahy",           "WI", "cudahy-wash"),
    ("Menomonee Falls",   "Menomonee Falls",  "WI", "menomonee-falls-wash"),
    ("Rawson Wash",       "Franklin",         "WI", "rawson-wash"),
    ("Howell",            "Milwaukee",        "WI", "howell"),
    ("Oklahoma Ave",      "Milwaukee",        "WI", "oklahoma-ave"),
    ("Good Hope",         "Milwaukee",        "WI", "good-hope"),
    ("Miller Park Way",   "Milwaukee",        "WI", "miller-park-way"),
    ("Greenfield",        "Milwaukee",        "WI", "greenfield"),
    ("Oshkosh",           "Oshkosh",          "WI", "oshkosh"),
    ("Brookfield",        "Brookfield",       "WI", "brookfield"),
    ("Park St",           "Madison",          "WI", "park-st"),
    ("Washington",        "Madison",          "WI", "washington"),
]


def main():
    print("=" * 60)
    print("Mister Car Wash Address Scraper")
    print("=" * 60)
    print()

    # Install dependencies if needed
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "selenium", "webdriver-manager"])
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service

    # Check if output file already exists — resume from where we left off
    done_slugs = set()
    rows = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                done_slugs.add(row['slug'])
        print(f"Resuming — {len(done_slugs)} already scraped.")

    remaining = [s for s in STORES if s[3] not in done_slugs]
    print(f"Stores to scrape: {len(remaining)} of {len(STORES)}")
    print()

    if not remaining:
        print("All stores already scraped!")
        return

    # Launch headless Chrome
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--log-level=3")

    print("Launching Chrome...")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    wait    = WebDriverWait(driver, 15)

    failed = []

    try:
        for i, (name, city, state, slug) in enumerate(remaining):
            url = f"https://mistercarwash.com/store/{slug}/"
            label = f"Mister Car Wash {name}, {city} {state}"
            print(f"[{i+1:3d}/{len(remaining)}] {label:55s}", end=" ", flush=True)

            address = ""
            try:
                driver.get(url)
                # Wait for the address element to appear
                # The address is in a <p> or <div> following an "ADDRESS" heading
                # Try multiple selectors used on the site
                selectors = [
                    "//strong[contains(text(),'ADDRESS')]/following-sibling::*[1]",
                    "//b[contains(text(),'ADDRESS')]/following-sibling::*[1]",
                    "//p[contains(@class,'address')]",
                    "//div[contains(@class,'address')]",
                    "//*[contains(text(),'ADDRESS')]/../following-sibling::*[1]",
                    # The snippet shows "ADDRESS" as bold label then address below
                    "//strong[text()='ADDRESS']/parent::*/following-sibling::p[1]",
                    "//strong[text()='ADDRESS']/following::text()[1]",
                ]

                for sel in selectors:
                    try:
                        el = wait.until(
                            EC.presence_of_element_located((By.XPATH, sel))
                        )
                        text = el.text.strip()
                        if text and len(text) > 3 and text != "ADDRESS":
                            address = text
                            break
                    except Exception:
                        continue

                # Fallback: search page source for address pattern
                if not address:
                    src = driver.page_source
                    import re
                    # Look for text after "ADDRESS" label
                    m = re.search(
                        r'ADDRESS\s*</(?:strong|b|p|div)[^>]*>\s*(?:<[^>]+>)?\s*([0-9][^\n<]{5,60})',
                        src, re.IGNORECASE
                    )
                    if m:
                        address = m.group(1).strip()

            except Exception as ex:
                failed.append((name, city, state, slug, str(ex)))
                print(f"ERROR: {ex}")
                continue

            if address:
                print(f"-> {address}")
            else:
                print("-> (address not found)")
                failed.append((name, city, state, slug, "not found"))

            row = {
                "slug":    slug,
                "name":    f"Mister Car Wash {name}",
                "city":    city,
                "state":   state,
                "address": address,
                "full_address": f"{address}, {city}, {state}" if address else "",
            }
            rows.append(row)

            # Write after every store so progress is saved
            with open(OUTPUT_FILE, "w", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writeheader()
                writer.writerows(rows)

            time.sleep(0.5)

    finally:
        driver.quit()

    print()
    found   = sum(1 for r in rows if r['address'])
    missing = sum(1 for r in rows if not r['address'])
    print(f"Complete:  {found}/{len(rows)} addresses found")
    print(f"Missing:   {missing}")
    print(f"Saved to:  {OUTPUT_FILE}")
    print()
    print("Next step: run geocode_mistercarwash.py to convert")
    print("addresses to coordinates and merge into pois.geojson")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
    print()
    input("Press Enter to close...")
