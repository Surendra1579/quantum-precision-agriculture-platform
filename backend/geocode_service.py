"""
Production Geocoding Service for Quantum Precision Agriculture Platform.
Provides high-accuracy coordinate resolution for Indian States, Districts, and Micro-zones
using OpenStreetMap Nominatim API, dynamic caching, and pre-compiled GIS centroid registries.
"""

import logging
import requests
from functools import lru_cache
from typing import Dict, Tuple, Optional, Any

logger = logging.getLogger("geocode_service")

# Comprehensive Indian State & District Centroids (WGS84 Lat/Lon)
INDIAN_DISTRICT_COORDINATES: Dict[Tuple[str, str], Tuple[float, float]] = {
    # Andhra Pradesh
    ("ANDHRA PRADESH", "GUNTUR"): (16.3067, 80.4365),
    ("ANDHRA PRADESH", "PRAKASAM"): (15.5057, 80.0499),
    ("ANDHRA PRADESH", "KRISHNA"): (16.1800, 81.1300),
    ("ANDHRA PRADESH", "ANAKAPALLI"): (17.6896, 83.0033),
    ("ANDHRA PRADESH", "VISAKHAPATNAM"): (17.6868, 83.2185),
    ("ANDHRA PRADESH", "EAST GODAVARI"): (16.9891, 82.2475),
    ("ANDHRA PRADESH", "WEST GODAVARI"): (16.7107, 81.0952),
    ("ANDHRA PRADESH", "NELLORE"): (14.4426, 79.9865),
    ("ANDHRA PRADESH", "ANANTAPUR"): (14.6819, 77.6006),
    ("ANDHRA PRADESH", "CHITTOOR"): (13.2172, 79.1003),
    ("ANDHRA PRADESH", "KURNOOL"): (15.8281, 78.0373),
    ("ANDHRA PRADESH", "KADAPA"): (14.4673, 78.8242),
    ("ANDHRA PRADESH", "SRIKAKULAM"): (18.2949, 83.8938),
    ("ANDHRA PRADESH", "VIZIANAGARAM"): (18.1067, 83.3956),
    ("ANDHRA PRADESH", "ELURU"): (16.7107, 81.0952),
    ("ANDHRA PRADESH", "KAKINADA"): (16.9891, 82.2475),
    ("ANDHRA PRADESH", "NTR"): (16.5062, 80.6480),
    ("ANDHRA PRADESH", "BAPATLA"): (15.9042, 80.4674),
    ("ANDHRA PRADESH", "PALNADU"): (16.2361, 80.0531),
    ("ANDHRA PRADESH", "TIRUPATI"): (13.6288, 79.4192),
    ("ANDHRA PRADESH", "NANDYAL"): (15.4786, 78.4836),
    ("ANDHRA PRADESH", "ALLURI SITHARAMA RAJU"): (17.8427, 82.2530),
    ("ANDHRA PRADESH", "PARVATHIPURAM MANYAM"): (18.7800, 83.4283),
    ("ANDHRA PRADESH", "DR. B.R. AMBEDKAR KONASEEMA"): (16.5772, 81.9963),
    ("ANDHRA PRADESH", "ANNAMAYYA"): (14.0416, 79.0833),
    ("ANDHRA PRADESH", "SRI SATHYA SAI"): (14.1670, 77.8118),

    # Telangana
    ("TELANGANA", "HYDERABAD"): (17.3850, 78.4867),
    ("TELANGANA", "WARANGAL"): (17.9689, 79.5941),
    ("TELANGANA", "KARIMNAGAR"): (18.4386, 79.1288),
    ("TELANGANA", "KHAMMAM"): (17.2473, 80.1514),
    ("TELANGANA", "NALGONDA"): (17.0575, 79.2684),
    ("TELANGANA", "NIZAMABAD"): (18.6725, 78.0941),
    ("TELANGANA", "MEDAK"): (18.0485, 78.2612),
    ("TELANGANA", "RANGAREDDY"): (17.4399, 78.4983),
    ("TELANGANA", "SIDDIPET"): (18.1018, 78.8520),
    ("TELANGANA", "MAHABUBNAGAR"): (16.7488, 77.9856),
    ("TELANGANA", "ADILABAD"): (19.6641, 78.5320),
    ("TELANGANA", "SANGAREDDY"): (17.6256, 78.0848),
    ("TELANGANA", "BHADRADRI KOTHAGUDEM"): (17.5540, 80.6175),
    ("TELANGANA", "JAGTIAL"): (18.7950, 78.9130),
    ("TELANGANA", "SURYAPET"): (17.1439, 79.6239),

    # Karnataka
    ("KARNATAKA", "BENGALURU"): (12.9716, 77.5946),
    ("KARNATAKA", "BENGALURU URBAN"): (12.9716, 77.5946),
    ("KARNATAKA", "BENGALURU RURAL"): (13.2284, 77.5753),
    ("KARNATAKA", "MYSURU"): (12.2958, 76.6394),
    ("KARNATAKA", "BELAGAVI"): (15.8497, 74.4977),
    ("KARNATAKA", "DHARWAD"): (15.4589, 75.0078),
    ("KARNATAKA", "BALLARI"): (15.1394, 76.9214),
    ("KARNATAKA", "KALABURAGI"): (17.3297, 76.8343),
    ("KARNATAKA", "TUMAKURU"): (13.3409, 77.1010),
    ("KARNATAKA", "SHIVAMOGGA"): (13.9299, 75.5681),
    ("KARNATAKA", "MANGALURU"): (12.9141, 74.8560),
    ("KARNATAKA", "DAKSHINA KANNADA"): (12.8703, 75.2514),
    ("KARNATAKA", "UDUPI"): (13.3409, 74.7421),
    ("KARNATAKA", "HASSAN"): (13.0033, 76.1004),
    ("KARNATAKA", "VIJAYAPURA"): (16.8302, 75.7100),
    ("KARNATAKA", "DAVANAGERE"): (14.4644, 75.9218),
    ("KARNATAKA", "RAICHUR"): (16.2120, 77.3439),

    # Tamil Nadu
    ("TAMIL NADU", "CHENNAI"): (13.0827, 80.2707),
    ("TAMIL NADU", "COIMBATORE"): (11.0168, 76.9558),
    ("TAMIL NADU", "MADURAI"): (9.9252, 78.1198),
    ("TAMIL NADU", "SALEM"): (11.6643, 78.1460),
    ("TAMIL NADU", "THANJAVUR"): (10.7870, 79.1378),
    ("TAMIL NADU", "ERODE"): (11.3410, 77.7172),
    ("TAMIL NADU", "TIRUCHIRAPPALLI"): (10.7905, 78.7047),
    ("TAMIL NADU", "VELLORE"): (12.9165, 79.1325),
    ("TAMIL NADU", "TIRUNELVELI"): (8.7139, 77.7567),
    ("TAMIL NADU", "DINDIGUL"): (10.3673, 77.9803),
    ("TAMIL NADU", "KANCHEEPURAM"): (12.8342, 79.7036),
    ("TAMIL NADU", "CUDDALORE"): (11.7480, 79.7714),
    ("TAMIL NADU", "TIRUPPUR"): (11.1085, 77.3411),

    # Maharashtra
    ("MAHARASHTRA", "PUNE"): (18.5204, 73.8567),
    ("MAHARASHTRA", "NASHIK"): (19.9975, 73.7898),
    ("MAHARASHTRA", "NAGPUR"): (21.1458, 79.0882),
    ("MAHARASHTRA", "AHMEDNAGAR"): (19.0948, 74.7480),
    ("MAHARASHTRA", "SOLAPUR"): (17.6599, 75.9064),
    ("MAHARASHTRA", "AURANGABAD"): (19.8762, 75.3433),
    ("MAHARASHTRA", "CHHATRAPATI SAMBHAJINAGAR"): (19.8762, 75.3433),
    ("MAHARASHTRA", "KOLHAPUR"): (16.7050, 74.2433),
    ("MAHARASHTRA", "MUMBAI"): (19.0760, 72.8777),
    ("MAHARASHTRA", "SATARA"): (17.6805, 74.0183),
    ("MAHARASHTRA", "SANGLI"): (16.8524, 74.5815),
    ("MAHARASHTRA", "JALGAON"): (21.0077, 75.5626),
    ("MAHARASHTRA", "AMRAVATI"): (20.9374, 77.7796),
    ("MAHARASHTRA", "NANDED"): (19.1383, 77.3210),
    ("MAHARASHTRA", "LATUR"): (18.4088, 76.5604),

    # Gujarat
    ("GUJARAT", "AHMEDABAD"): (23.0225, 72.5714),
    ("GUJARAT", "AMRELI"): (21.6032, 71.2221),
    ("GUJARAT", "ANAND"): (22.5645, 72.9289),
    ("GUJARAT", "SURAT"): (21.1702, 72.8311),
    ("GUJARAT", "RAJKOT"): (22.3039, 70.8022),
    ("GUJARAT", "BHAVNAGAR"): (21.7645, 72.1519),
    ("GUJARAT", "VADODARA"): (22.3072, 73.1812),
    ("GUJARAT", "JAMNAGAR"): (22.4707, 70.0577),
    ("GUJARAT", "JUNAGADH"): (21.5222, 70.4579),
    ("GUJARAT", "KHEDA"): (22.7547, 72.6841),
    ("GUJARAT", "GANDHINAGAR"): (23.2156, 72.6369),
    ("GUJARAT", "MEHSANA"): (23.5880, 72.3693),
    ("GUJARAT", "BHARUCH"): (21.7051, 72.9959),

    # Punjab & Haryana
    ("PUNJAB", "LUDHIANA"): (30.9010, 75.8573),
    ("PUNJAB", "AMRITSAR"): (31.6340, 74.8723),
    ("PUNJAB", "JALANDHAR"): (31.3260, 75.5762),
    ("PUNJAB", "PATIALA"): (30.3398, 76.3869),
    ("PUNJAB", "BATHINDA"): (30.2110, 74.9455),
    ("PUNJAB", "HOSHIARPUR"): (31.5143, 75.9115),
    ("HARYANA", "KARNAL"): (29.6857, 76.9905),
    ("HARYANA", "AMBALA"): (30.3782, 76.7767),
    ("HARYANA", "HISAR"): (29.1492, 75.7217),
    ("HARYANA", "ROHTAK"): (28.8955, 76.6066),
    ("HARYANA", "GURUGRAM"): (28.4595, 77.0266),
    ("HARYANA", "FARIDABAD"): (28.4089, 77.3178),
    ("HARYANA", "PANIPAT"): (29.3909, 76.9635),

    # Uttar Pradesh
    ("UTTAR PRADESH", "LUCKNOW"): (26.8467, 80.9462),
    ("UTTAR PRADESH", "VARANASI"): (25.3176, 82.9739),
    ("UTTAR PRADESH", "KANPUR"): (26.4499, 80.3319),
    ("UTTAR PRADESH", "KANPUR NAGAR"): (26.4499, 80.3319),
    ("UTTAR PRADESH", "AGRA"): (27.1767, 78.0081),
    ("UTTAR PRADESH", "PRAYAGRAJ"): (25.4358, 81.8463),
    ("UTTAR PRADESH", "MEERUT"): (28.9845, 77.7064),
    ("UTTAR PRADESH", "BAREILLY"): (28.3670, 79.4304),
    ("UTTAR PRADESH", "GORAKHPUR"): (26.7606, 83.3732),
    ("UTTAR PRADESH", "ALIGARH"): (27.8974, 78.0880),
    ("UTTAR PRADESH", "AYODHYA"): (26.7922, 82.1998),

    # West Bengal, Bihar, MP, Rajasthan, Kerala, Odisha
    ("WEST BENGAL", "KOLKATA"): (22.5726, 88.3639),
    ("WEST BENGAL", "BURDWAN"): (23.2324, 87.8615),
    ("WEST BENGAL", "PURBA BARDHAMAN"): (23.2324, 87.8615),
    ("WEST BENGAL", "HOOGHLY"): (22.9034, 88.3966),
    ("WEST BENGAL", "HOWRAH"): (22.5958, 88.2636),
    ("BIHAR", "PATNA"): (25.5941, 85.1376),
    ("BIHAR", "GAYA"): (24.7914, 85.0002),
    ("BIHAR", "MUZAFFARPUR"): (26.1209, 85.3647),
    ("BIHAR", "BHAGALPUR"): (25.2425, 86.9842),
    ("RAJASTHAN", "JAIPUR"): (26.9124, 75.7873),
    ("RAJASTHAN", "JODHPUR"): (26.2389, 73.0243),
    ("RAJASTHAN", "KOTA"): (25.2138, 75.8648),
    ("RAJASTHAN", "UDAIPUR"): (24.5854, 73.7125),
    ("MADHYA PRADESH", "BHOPAL"): (23.2599, 77.4126),
    ("MADHYA PRADESH", "INDORE"): (22.7196, 75.8577),
    ("MADHYA PRADESH", "GWALIOR"): (26.2183, 78.1828),
    ("MADHYA PRADESH", "JABALPUR"): (23.1815, 79.9864),
    ("KERALA", "THIRUVANANTHAPURAM"): (8.5241, 76.9366),
    ("KERALA", "KOCHI"): (9.9312, 76.2673),
    ("KERALA", "ERNAKULAM"): (9.9816, 76.2999),
    ("KERALA", "PALAKKAD"): (10.7867, 76.6548),
    ("KERALA", "KOZHIKODE"): (11.2588, 75.7804),
    ("ODISHA", "BHUBANESWAR"): (20.2961, 85.8245),
    ("ODISHA", "CUTTACK"): (20.4625, 85.8828),
    ("ODISHA", "PURI"): (19.8135, 85.8312),
    ("ODISHA", "SAMBALPUR"): (21.4669, 83.9812),

    # Other States & Territories
    ("ASSAM", "GUWAHATI"): (26.1445, 91.7362),
    ("ASSAM", "KAMRUP"): (26.1445, 91.7362),
    ("CHHATTISGARH", "RAIPUR"): (21.2514, 81.6296),
    ("CHHATTISGARH", "BILASPUR"): (22.0797, 82.1409),
    ("JHARKHAND", "RANCHI"): (23.3441, 85.3096),
    ("JHARKHAND", "JAMSHEDPUR"): (22.8046, 86.2029),
    ("UTTARAKHAND", "DEHRADUN"): (30.3165, 78.0322),
    ("UTTARAKHAND", "HARIDWAR"): (29.9457, 78.1642),
    ("HIMACHAL PRADESH", "SHIMLA"): (31.1048, 77.1734),
    ("GOA", "NORTH GOA"): (15.5494, 73.8828),
    ("GOA", "SOUTH GOA"): (15.2993, 74.1240),
    ("DELHI", "NEW DELHI"): (28.6139, 77.2090),
}

# State Centroids
STATE_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "ANDHRA PRADESH": (15.9129, 79.7400),
    "TELANGANA": (17.8749, 78.9429),
    "TAMIL NADU": (11.1271, 78.6569),
    "KARNATAKA": (15.3173, 75.7139),
    "MAHARASHTRA": (19.7515, 75.7139),
    "GUJARAT": (22.2587, 71.1924),
    "PUNJAB": (31.1471, 75.3412),
    "HARYANA": (29.0588, 76.0856),
    "UTTAR PRADESH": (26.8467, 80.9462),
    "WEST BENGAL": (22.9868, 87.8550),
    "BIHAR": (25.0961, 85.3131),
    "RAJASTHAN": (27.0238, 74.2179),
    "MADHYA PRADESH": (22.9734, 78.6569),
    "KERALA": (10.8505, 76.2711),
    "ODISHA": (20.9517, 85.0985),
    "ASSAM": (26.2006, 92.9376),
    "CHHATTISGARH": (21.2787, 81.8661),
    "JHARKHAND": (23.6102, 85.2799),
    "UTTARAKHAND": (30.0668, 79.0193),
    "HIMACHAL PRADESH": (31.1048, 77.1734),
    "GOA": (15.2993, 74.1240),
    "DELHI": (28.7041, 77.1025),
    "DEFAULT": (20.5937, 78.9629)
}

# In-memory LRU Cache for external API queries
_GEOCODE_CACHE: Dict[str, Tuple[float, float, str]] = {}


def clean_str(s: Optional[str]) -> str:
    """Helper to clean and normalize search strings."""
    return (s or "").strip().upper()


def query_nominatim(state: str, district: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """
    Queries OpenStreetMap Nominatim API for high-precision GIS coordinates.
    Follows OSM Nominatim Usage Policy (User-Agent header, timeout).
    """
    try:
        query_parts = []
        if district:
            query_parts.append(district)
        if state:
            query_parts.append(state)
        query_parts.append("India")
        q = ", ".join(query_parts)

        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            "User-Agent": "QuantumAgriAI-PrecisionDSS/3.0 (agri-ai@support.org)",
            "Accept": "application/json"
        }
        params = {
            "q": q,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "countrycodes": "in"
        }
        res = requests.get(url, headers=headers, params=params, timeout=3.5)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                logger.info(f"[Nominatim Geocode OK] {q} -> ({lat}, {lon})")
                return lat, lon
    except Exception as e:
        logger.warning(f"[Nominatim Geocode Warning] Query failed for '{state}, {district}': {e}")
    return None


def query_open_meteo(state: str, district: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """
    Secondary fallback: Queries Open-Meteo Geocoding API.
    """
    try:
        query_name = f"{district} {state}".strip() if district else state
        url = "https://geocoding-api.open-meteo.com/v1/search"
        res = requests.get(url, params={"name": query_name, "count": 1, "format": "json"}, timeout=3.0)
        if res.status_code == 200:
            data = res.json()
            if "results" in data and len(data["results"]) > 0:
                lat = float(data["results"][0]["latitude"])
                lon = float(data["results"][0]["longitude"])
                logger.info(f"[Open-Meteo Geocode OK] {query_name} -> ({lat}, {lon})")
                return lat, lon
    except Exception as e:
        logger.debug(f"[Open-Meteo Geocode Warning] Query failed for '{query_name}': {e}")
    return None


def resolve_coordinates(state: str, district: Optional[str] = None) -> Optional[Tuple[float, float, str]]:
    """
    Multi-tier geocoding resolver:
    1. In-memory cache
    2. High-precision curated Indian district database (0ms lookup)
    3. OpenStreetMap Nominatim API
    4. Open-Meteo Geocoding API
    5. State Centroid fallback
    """
    st_clean = clean_str(state)
    dist_clean = clean_str(district)

    if not st_clean and not dist_clean:
        return None

    cache_key = f"{st_clean}::{dist_clean}"
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    # Tier 1: Exact Match in Curated GIS Database
    if (st_clean, dist_clean) in INDIAN_DISTRICT_COORDINATES:
        lat, lon = INDIAN_DISTRICT_COORDINATES[(st_clean, dist_clean)]
        _GEOCODE_CACHE[cache_key] = (lat, lon, "curated_database")
        return lat, lon, "curated_database"

    # Tier 1b: State Centroid if only state is queried
    if not dist_clean and st_clean in STATE_CENTROIDS:
        lat, lon = STATE_CENTROIDS[st_clean]
        _GEOCODE_CACHE[cache_key] = (lat, lon, "state_centroid")
        return lat, lon, "state_centroid"

    # Tier 2: Substring Match in GIS Database
    if dist_clean:
        for (s, d), (lat, lon) in INDIAN_DISTRICT_COORDINATES.items():
            if s == st_clean and (d in dist_clean or dist_clean in d):
                _GEOCODE_CACHE[cache_key] = (lat, lon, "curated_database")
                return lat, lon, "curated_database"
        # Match district regardless of state spelling variant
        for (s, d), (lat, lon) in INDIAN_DISTRICT_COORDINATES.items():
            if d == dist_clean:
                _GEOCODE_CACHE[cache_key] = (lat, lon, "curated_database")
                return lat, lon, "curated_database"

    # Tier 3: OpenStreetMap Nominatim API
    nom_coords = query_nominatim(state, district)
    if nom_coords:
        lat, lon = nom_coords
        _GEOCODE_CACHE[cache_key] = (lat, lon, "nominatim")
        return lat, lon, "nominatim"

    # Tier 4: Open-Meteo Geocoding
    meteo_coords = query_open_meteo(state, district)
    if meteo_coords:
        lat, lon = meteo_coords
        _GEOCODE_CACHE[cache_key] = (lat, lon, "open_meteo")
        return lat, lon, "open_meteo"

    # Tier 5: State Centroid Fallback
    if st_clean in STATE_CENTROIDS:
        lat, lon = STATE_CENTROIDS[st_clean]
        _GEOCODE_CACHE[cache_key] = (lat, lon, "state_centroid")
        return lat, lon, "state_centroid"

    for s, (lat, lon) in STATE_CENTROIDS.items():
        if s in st_clean or st_clean in s:
            _GEOCODE_CACHE[cache_key] = (lat, lon, "state_centroid")
            return lat, lon, "state_centroid"

    return None
