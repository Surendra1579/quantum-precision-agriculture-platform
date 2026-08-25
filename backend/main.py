"""
Quantum AI Precision Agriculture Decision Support Platform - Main FastAPI Application.
Integrates Hybrid Quantum Machine Learning (PennyLane + Qiskit + PyTorch), Satellite Earth Observation,
Soil Intelligence, Advanced Agro-Meteorology, 4R Fertilizer Stewardship, and Per-Plot Decision Support.
"""

import os
import sys
from pathlib import Path
from datetime import date, datetime
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Database & Storage
from database.connection import init_db, get_db
from database.repository import get_all_fields, get_recent_predictions, get_all_farms, log_prediction

# Quantum Inference & Training
from quantum.inference import quantum_engine
from quantum.train_crop_quantum import train_crop_yield_quantum
from quantum.train_price_quantum import train_price_quantum
from quantum.quantum_utils import get_circuit_metadata
from quantum.config import QUANTUM_CIRCUIT_CFG, QUANTUM_DEVICE_CFG

# Existing Services (Preserved for 100% Compatibility)
from rainfall_service import get_annual_rainfall
from satellite_service import fetch_satellite_agro_indices

# New Precision Agriculture Modules
from satellite.satellite_routes import router as satellite_router
from satellite.satellite_service import satellite_service
from soil.soil_api import router as soil_router
from soil.soil_service import soil_service
from weather.weather_routes import router as weather_router
from weather.weather_service import weather_service
from recommendation.recommendation_api import router as recommendation_router
from recommendation.recommendation_engine import recommendation_engine
from plot.plot_routes import router as plot_router, PlotAnalysisRequest
from plot.plot_service import plot_service

# =========================================================
# PATHS & DATASETS
# =========================================================

PRICE_DATA_PATH = BASE_DIR / "data" / "commodity_price.csv"

# Load Historical Price Dataset
try:
    price_data = pd.read_csv(PRICE_DATA_PATH)
    price_data = price_data.rename(
        columns={
            "District Name": "District",
            "Market Name": "Market",
            "Min Price (Rs./Quintal)": "Min_Price",
            "Max Price (Rs./Quintal)": "Max_Price",
            "Modal Price (Rs./Quintal)": "Modal_Price",
            "Min_x0020_Price": "Min_Price",
            "Max_x0020_Price": "Max_Price",
            "Modal_x0020_Price": "Modal_Price",
            "Price Date": "Arrival_Date",
        }
    )
    price_data = price_data.drop(columns=["Sl no."], errors="ignore")
    price_data["Arrival_Date"] = pd.to_datetime(price_data["Arrival_Date"], dayfirst=True, errors="coerce")
    price_data["Modal_Price"] = pd.to_numeric(price_data["Modal_Price"], errors="coerce")
    price_data = price_data.dropna(subset=["Arrival_Date", "Modal_Price"])
    price_data = price_data[price_data["Modal_Price"] > 0].copy()
    price_data = price_data.sort_values("Arrival_Date").reset_index(drop=True)
    print(f"[OK] Historical price data loaded successfully: {len(price_data)} records.")
except Exception as e:
    print(f"[WARNING] Could not load historical price data: {e}")
    price_data = pd.DataFrame()


import logging

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("precision_agri_api")

# =========================================================
# FASTAPI APP INITIALIZATION
# =========================================================

app = FastAPI(
    title="Quantum Precision Agriculture Decision Support Platform",
    description="Enterprise-grade Hybrid Quantum AI system for Precision Crop Yield, Commodity Price Forecasting, Satellite Intelligence, Soil Health, and Farm Planning.",
    version="3.0.0"
)

# Dynamic Production CORS Configuration
DEFAULT_ALLOWED_ORIGINS = [
    "https://quantum-precision-agriculture-platf.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

raw_origins = os.environ.get("ALLOWED_ORIGINS", "")
if raw_origins and raw_origins.strip() != "*":
    for o in raw_origins.split(","):
        clean_o = o.strip()
        if clean_o and clean_o not in DEFAULT_ALLOWED_ORIGINS:
            DEFAULT_ALLOWED_ORIGINS.append(clean_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize Database on Startup
@app.on_event("startup")
def on_startup():
    logger.info("Initializing SQLite database connection and ORM schemas...")
    init_db()
    logger.info("[OK] Production database initialized successfully.")

# Mount New Module Routers
app.include_router(satellite_router)
app.include_router(soil_router)
app.include_router(weather_router)
app.include_router(recommendation_router)
app.include_router(plot_router)

# Mount Frontend Static Directory
frontend_dir = BASE_DIR.parent / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


# =========================================================
# PYDANTIC SCHEMAS (100% Backward Compatible)
# =========================================================

class YieldInput(BaseModel):
    Crop: str
    Crop_Year: int = Field(default=2024)
    Season: str
    State: str
    District: Optional[str] = None
    Area: float = Field(default=10.0, description="Cultivated Area in Acres")
    Annual_Rainfall: Optional[float] = None
    Fertilizer: float = Field(default=800.0, description="Fertilizer in kg")
    Pesticide: float = Field(default=40.0, description="Pesticide in kg")


class PriceInput(BaseModel):
    State: str
    District: str
    Market: str
    Commodity: str
    Variety: str
    Grade: str
    Prediction_Date: date


# =========================================================
# STATE & DISTRICT DICTIONARIES
# =========================================================

STATE_ALIASES = {
    "uttarakhand": "uttrakhand",
    "uttrakhand": "uttrakhand",
    "jammu & kashmir": "jammu and kashmir",
    "jammu and kashmir": "jammu and kashmir",
}

ALL_STATE_DISTRICTS = {
    "Andhra Pradesh": [
        "Anakapalli", "Anantapur", "Annamayya", "Bapatla", "Chittoor", "Chittor",
        "East Godavari", "Eluru", "Guntur", "Kakinada", "Konaseema", "Krishna",
        "Kurnool", "NTR (Vijayawada)", "Nandyal", "Nellore", "Palnadu", "Prakasam",
        "Sri Sathya Sai", "Srikakulam", "Tirupati", "Visakhapatnam", "Vizianagaram",
        "West Godavari", "YSR Kadapa"
    ],
    "Arunachal Pradesh": [
        "Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang", "Kamle",
        "Kra Daadi", "Kurung Kumey", "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley",
        "Lower Siang", "Lower Subansiri", "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi",
        "Siang", "Tawang", "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang"
    ],
    "Assam": [
        "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang",
        "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat",
        "Hailakandi", "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong",
        "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari",
        "Sivasagar", "Sonitpur", "South Salmara-Mankachar", "Tinsukia", "Udalguri", "West Karbi Anglong"
    ],
    "Bihar": [
        "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur",
        "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad",
        "Kaimur", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani",
        "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas",
        "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan",
        "Supaul", "Vaishali", "West Champaran"
    ],
    "Chhattisgarh": [
        "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur",
        "Dantewada", "Dhamtari", "Durg", "Gariaband", "Gaurela-Pendra-Marwahi", "Janjgir-Champa",
        "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund",
        "Manendragarh-Chirmiri-Bharatpur", "Mohla-Manpur-Ambagarh Chowki", "Mungeli", "Narayanpur",
        "Raigarh", "Raipur", "Rajnandgaon", "Sarangarh-Bilaigarh", "Shakti", "Sukma", "Surajpur", "Surguja"
    ],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Banaskanth", "Bharuch",
        "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka",
        "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Junagarh", "Kheda",
        "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal",
        "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi",
        "Vadodara", "Vadodara(Baroda)", "Valsad"
    ],
    "Haryana": [
        "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram",
        "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh",
        "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa",
        "Sonipat", "Yamunanagar"
    ],
    "Himachal Pradesh": [
        "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti",
        "Mandi", "Shimla", "Sirmaur", "Solan", "Una"
    ],
    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa",
        "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma",
        "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahibganj",
        "Seraikela Kharsawan", "Simdega", "West Singhbhum"
    ],
    "Karnataka": [
        "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar",
        "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada",
        "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu",
        "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga",
        "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"
    ],
    "Kerala": [
        "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam",
        "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"
    ],
    "Madhya Pradesh": [
        "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul",
        "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia",
        "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore",
        "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur",
        "Morena", "Narsinghpur", "Neemuch", "Niwari", "Panna", "Raisen", "Rajgarh",
        "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur",
        "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"
    ],
    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana",
        "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna",
        "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded",
        "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad",
        "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"
    ],
    "Odisha": [
        "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", "Deogarh",
        "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi",
        "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj",
        "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"
    ],
    "Punjab": [
        "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur",
        "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Malerkotla", "Mansa",
        "Moga", "Muktsar", "Pathankot", "Patiala", "Rupnagar", "Sahibzada Ajit Singh Nagar", "Sangrur",
        "Shahid Bhagat Singh Nagar", "Sri Muktsar Sahib", "Tarn Taran"
    ],
    "Rajasthan": [
        "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner",
        "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Ganganagar",
        "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur",
        "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur",
        "Sikar", "Sirohi", "Tonk", "Udaipur"
    ],
    "Tamil Nadu": [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
        "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
        "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris",
        "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga",
        "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
        "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"
    ],
    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon",
        "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar",
        "Khammam", "Kumuram Bheem", "Mahabubabad", "Mahabubnagar", "Mancherial",
        "Medak", "Medchal Malkajgiri", "Mulugu", "Nalgonda", "Narayanpet",
        "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Ranga Reddy",
        "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
    ],
    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh",
        "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti",
        "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah",
        "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur",
        "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi",
        "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri", "Kushinagar", "Lalitpur",
        "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad",
        "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur",
        "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur",
        "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
    ],
    "Uttarakhand": [
        "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital",
        "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"
    ],
    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling",
        "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda",
        "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur",
        "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"
    ]
}

DISTRICT_MARKETS = {
    "guntur": ["Guntur Chilli Yard (APMC)", "Guntur Wholesale Grain Market", "Tenali Mandi", "Narasaraopet Market"],
    "krishna": ["Vijayawada APMC Mandi", "Gudivada Grain Market", "Machilipatnam Market", "Jaggaiahpeta Mandi"],
    "chittoor": ["Chittoor APMC Mandi", "Kalikiri", "Madanapalle Tomato Market", "Punganur Mandi", "Vayalapadu"],
    "chittor": ["Chittoor APMC Mandi", "Kalikiri", "Madanapalle Tomato Market", "Punganur Mandi", "Vayalapadu"],
    "east godavari": ["Kakinada Commercial Mandi", "Rajahmundry Grain Market", "Ravulapalem Banana Market"],
    "west godavari": ["Eluru APMC Market", "Tadepalligudem Mandi", "Bhimavaram Market", "Tanuku Mandi"],
    "kurnool": ["Kurnool Main Mandi", "Yemmiganur Market", "Adoni Cotton Market", "Nandyal Mandi"],
    "nellore": ["Nellore Grain Mandi", "Gudur Market", "Kavali Market"],
    "anantapur": ["Anantapur APMC Mandi", "Hindupur Market", "Kalyandurg Market"],
    "visakhapatnam": ["Anakapalle Jaggery Mandi", "Visakhapatnam APMC Market", "Bheemunipatnam Market"],
    "hyderabad": ["Bowenpally Agricultural Market", "Gudimalkapur Mandi", "Kothapet Fruit Market"],
    "warangal": ["Warangal Grain & Chilli Yard", "Khammam Mandi", "Narsampet Market"],
    "chennai": ["Koyambedu Wholesale Market Complex"],
    "coimbatore": ["Mettupalayam Market", "Coimbatore APMC Mandi", "Pollachi Market"],
    "madurai": ["Mattuthavani Central Market", "Madurai APMC Mandi"],
    "bengaluru urban": ["Yeshwanthpur APMC Yard", "Binny Mill Market", "KR Market"],
    "pune": ["Gultekdi Market Yard", "Pimpri Mandi"],
    "nashik": ["Lasalgaon Onion Yard (Asia's Largest)", "Pimplegaon Mandi", "Nashik APMC"],
    "ahmedabad": ["Jamalpur Wholesale Market", "Vasna APMC Market", "Naroda Mandi"],
    "amreli": ["Damnagar Market", "Savarkundla Market", "Amreli Main Mandi"],
}


# =========================================================
# CORE ENDPOINTS & DASHBOARD AGGREGATOR
# =========================================================

@app.get("/")
def home():
    """Root endpoint returning system health and quantum precision agriculture telemetry."""
    status = quantum_engine.get_status()
    return {
        "message": "Quantum AI Precision Agriculture Decision Support System is running",
        "version": "3.0.0 (Hybrid Quantum Machine Learning & Earth Observation)",
        "quantum_framework": status["quantum_framework"],
        "yield_model_loaded": status["models"]["quantum_crop_yield"]["loaded"],
        "price_model_loaded": status["models"]["quantum_commodity_price"]["loaded"],
        "historical_price_rows": len(price_data),
        "app_ui_url": "/app/"
    }


@app.get("/health")
def health():
    """Health check endpoint for orchestrators and status monitoring."""
    status = quantum_engine.get_status()
    return {
        "status": "healthy",
        "yield_model": "loaded" if status["models"]["quantum_crop_yield"]["loaded"] else "not loaded",
        "price_model": "loaded" if status["models"]["quantum_commodity_price"]["loaded"] else "not loaded",
        "price_data": "loaded" if not price_data.empty else "not loaded",
        "quantum_backend": status["device_backend"],
        "qubits_yield": status["models"]["quantum_crop_yield"]["qubits"],
        "qubits_price": status["models"]["quantum_commodity_price"]["qubits"]
    }


@app.get("/geocode", tags=["Geospatial & Geocoding"])
def geocode_location(
    state: str = Query(..., description="Indian State Name (e.g. Andhra Pradesh)"),
    district: Optional[str] = Query(None, description="District Name (e.g. Prakasam, Guntur, Anakapalli)")
):
    """
    Geocodes State and District to WGS84 Latitude and Longitude coordinates.
    Utilizes OpenStreetMap Nominatim, in-memory LRU caching, and Indian GIS boundary centroids.
    """
    from geocode_service import resolve_coordinates
    coords = resolve_coordinates(state, district)
    if not coords:
        raise HTTPException(status_code=404, detail="Location not found.")

    lat, lon, source = coords
    return {
        "state": state,
        "district": district or state,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "source": source
    }


@app.get("/dashboard")
def get_dashboard_summary(
    state: str = Query("Andhra Pradesh"),
    district: str = Query("Guntur"),
    db: Session = Depends(get_db)
):
    """
    Executive Dashboard Aggregator.
    Returns composite KPIs: Quantum status, satellite field health, active weather alerts,
    registered farm plots count, and recent precision predictions.
    """
    q_status = quantum_engine.get_status()
    sat_summary = satellite_service.fetch_satellite_data(state=state, district=district)
    weather_summary = weather_service.get_weather_intelligence(state=state, district=district)
    soil_summary = soil_service.get_soil_profile(state=state, district=district)

    registered_fields = get_all_fields(db) if db else []
    recent_preds = get_recent_predictions(db, limit=5) if db else []

    return {
        "success": True,
        "location": {"state": state, "district": district},
        "kpi_cards": {
            "quantum_state": {
                "framework": "PennyLane + Qiskit HQNN/VQR",
                "backend": q_status["device_backend"],
                "yield_model_active": q_status["models"]["quantum_crop_yield"]["loaded"],
                "price_model_active": q_status["models"]["quantum_commodity_price"]["loaded"],
                "qubits": 8
            },
            "satellite_health": {
                "ndvi": sat_summary["indices"]["ndvi"],
                "evi": sat_summary["indices"]["evi"],
                "vhi": sat_summary["indices"]["vhi"],
                "status": sat_summary["classifications"]["overall_field_assessment"]["overall_status"],
                "color": sat_summary["classifications"]["overall_field_assessment"]["badge_color"]
            },
            "weather_alerts": {
                "temperature_c": weather_summary["current_weather"]["temperature_c"],
                "humidity_percent": weather_summary["current_weather"]["relative_humidity_percent"],
                "et0_mm": weather_summary["current_weather"]["evapotranspiration_et0_mm"],
                "active_alerts_count": weather_summary["alerts"]["total_alerts_count"],
                "alerts": weather_summary["alerts"]["active_alerts"]
            },
            "soil_fertility": {
                "soil_health_score": soil_summary["health_evaluation"]["soil_health_score"],
                "soil_grade": soil_summary["health_evaluation"]["soil_grade"],
                "badge_color": soil_summary["health_evaluation"]["badge_color"]
            },
            "farm_management": {
                "registered_plots_count": len(registered_fields),
                "plots": [f.to_dict() for f in registered_fields[:5]]
            }
        },
        "recent_predictions": [p.to_dict() for p in recent_preds]
    }


# Standalone Route: POST /plot-analysis
@app.post("/plot-analysis")
def plot_analysis_direct_route(data: PlotAnalysisRequest):
    """Direct alias for /plots/analyze."""
    return plot_service.analyze_plot(
        plot_name=data.plot_name,
        crop=data.crop,
        state=data.state,
        district=data.district,
        area_acres=data.area_acres,
        season=data.season,
        crop_year=data.crop_year,
        boundary_geojson=data.boundary_geojson,
        center_lat=data.center_lat,
        center_lon=data.center_lon,
        soil_type=data.soil_type
    )


@app.get("/model-status")
def get_model_status():
    """Detailed quantum model specifications, architecture, and training status."""
    return quantum_engine.get_status()


@app.get("/quantum/circuit")
def get_quantum_circuits():
    """Returns quantum circuit architecture, gate counts, depth, and ASCII diagrams."""
    return {
        "crop_yield_circuit": get_circuit_metadata(
            n_qubits=QUANTUM_CIRCUIT_CFG.n_qubits_yield,
            n_layers=QUANTUM_CIRCUIT_CFG.n_layers_yield
        ),
        "commodity_price_circuit": get_circuit_metadata(
            n_qubits=QUANTUM_CIRCUIT_CFG.n_qubits_price,
            n_layers=QUANTUM_CIRCUIT_CFG.n_layers_price
        )
    }


@app.get("/satellite-weather")
def get_satellite_weather(state: str, district: Optional[str] = None):
    """Retrieves live and satellite-derived vegetation indices (NDVI, EVI, Soil Moisture, LST)."""
    return fetch_satellite_agro_indices(state, district)


# =========================================================
# PREDICTION ENDPOINTS (100% Backward Compatible)
# =========================================================

def _execute_yield_prediction(data: YieldInput, db: Optional[Session] = None) -> Dict[str, Any]:
    if quantum_engine.yield_model is None:
        raise HTTPException(
            status_code=503,
            detail="Quantum Crop Yield Model is currently loading or not trained. Trigger /train-crop first."
        )

    try:
        rainfall_val = data.Annual_Rainfall
        rainfall_source = "User Input"

        if rainfall_val is None or rainfall_val <= 0:
            district_name = data.District if data.District else "Default"
            rainfall_val, rainfall_source = get_annual_rainfall(
                state=data.State,
                district=district_name,
                crop_year=data.Crop_Year
            )

        satellite_indices = fetch_satellite_agro_indices(data.State, data.District)

        result = quantum_engine.predict_crop_yield(
            crop=data.Crop,
            crop_year=data.Crop_Year,
            season=data.Season,
            state=data.State,
            area_acres=data.Area,
            annual_rainfall=rainfall_val,
            fertilizer=data.Fertilizer,
            pesticide=data.Pesticide,
            satellite_indices=satellite_indices
        )

        result["annual_rainfall_used"] = rainfall_val
        result["rainfall_source"] = rainfall_source
        result["satellite_data"] = satellite_indices
        result["model_architecture"] = "Hybrid Quantum-Classical Neural Network (8 Qubits)"

        # Log prediction to database
        if db:
            log_prediction(
                db=db,
                prediction_type="crop_yield",
                input_params=data.dict(),
                output_results=result,
                quantum_confidence=result.get("quantum_confidence_score", 80.0)
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quantum Yield Prediction failed: {str(e)}")


@app.post("/predict-yield")
def predict_yield(data: YieldInput, db: Session = Depends(get_db)):
    """Primary Crop Yield Prediction API powered by Hybrid Quantum Neural Network."""
    return _execute_yield_prediction(data, db=db)


@app.post("/predict-crop")
def predict_crop(data: YieldInput, db: Session = Depends(get_db)):
    """Alias for Crop Yield Prediction API."""
    return _execute_yield_prediction(data, db=db)


@app.post("/predict-price")
def predict_price(data: PriceInput, db: Session = Depends(get_db)):
    """Primary Commodity Price Forecast API powered by Variational Quantum Regressor."""
    if quantum_engine.price_model is None:
        raise HTTPException(
            status_code=503,
            detail="Quantum Commodity Price Model is currently loading or not trained. Trigger /train-price first."
        )

    try:
        prediction_date = pd.Timestamp(data.Prediction_Date)
        
        filtered = price_data.copy() if not price_data.empty else pd.DataFrame()
        if not filtered.empty:
            filtered = filtered[
                (filtered["State"].astype(str).str.strip().str.lower() == data.State.strip().lower()) &
                (filtered["District"].astype(str).str.strip().str.lower() == data.District.strip().lower()) &
                (filtered["Commodity"].astype(str).str.strip().str.lower() == data.Commodity.strip().lower())
            ]
            filtered = filtered[filtered["Arrival_Date"] < prediction_date].sort_values("Arrival_Date")

        avail_prices = filtered["Modal_Price"].dropna().tolist() if not filtered.empty else [2500.0]
        if len(avail_prices) < 7:
            first_p = avail_prices[0]
            historical_prices = ([first_p] * (7 - len(avail_prices))) + avail_prices
        else:
            historical_prices = avail_prices[-7:]

        price_lag_1 = float(historical_prices[-1])
        price_lag_7 = float(historical_prices[0])
        rolling_mean_7 = float(sum(historical_prices) / len(historical_prices))

        result = quantum_engine.predict_commodity_price(
            state=data.State,
            district=data.District,
            market=data.Market,
            commodity=data.Commodity,
            variety=data.Variety,
            grade=data.Grade,
            year=prediction_date.year,
            month=prediction_date.month,
            day=prediction_date.day,
            day_of_week=prediction_date.dayofweek,
            price_lag_1=price_lag_1,
            price_lag_7=price_lag_7,
            rolling_mean_7=rolling_mean_7
        )

        result["commodity"] = data.Commodity
        result["market"] = data.Market
        result["prediction_date"] = str(data.Prediction_Date)
        result["model_architecture"] = "Variational Quantum Regressor (8 Qubits)"

        # Log prediction to database
        if db:
            log_prediction(
                db=db,
                prediction_type="commodity_price",
                input_params=data.dict(),
                output_results=result,
                quantum_confidence=result.get("quantum_confidence_score", 80.0)
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quantum Price Forecast failed: {str(e)}")


# =========================================================
# TRAINING ENDPOINTS
# =========================================================

@app.post("/train-crop")
def trigger_train_crop(background_tasks: BackgroundTasks, sync: bool = Query(False, description="Run synchronously")):
    """Triggers retraining of the Hybrid Quantum Crop Yield Model."""
    if sync:
        metrics = train_crop_yield_quantum()
        quantum_engine.load_models()
        return {"message": "Quantum Crop Yield Training complete", "metrics": metrics}

    background_tasks.add_task(lambda: (train_crop_yield_quantum(), quantum_engine.load_models()))
    return {"message": "Quantum Crop Yield Model training initiated in background", "status": "processing"}


@app.post("/train-price")
def trigger_train_price(background_tasks: BackgroundTasks, sync: bool = Query(False, description="Run synchronously")):
    """Triggers retraining of the Variational Quantum Commodity Price Model."""
    if sync:
        metrics = train_price_quantum()
        quantum_engine.load_models()
        return {"message": "Quantum Commodity Price Training complete", "metrics": metrics}

    background_tasks.add_task(lambda: (train_price_quantum(), quantum_engine.load_models()))
    return {"message": "Quantum Commodity Price Model training initiated in background", "status": "processing"}


# =========================================================
# DROPDOWN & LOOKUP ENDPOINTS (100% Backward Compatible)
# =========================================================

@app.get("/states")
def get_states():
    if price_data.empty:
        return sorted(list(ALL_STATE_DISTRICTS.keys()))

    raw_states = price_data["State"].dropna().astype(str).str.strip().unique().tolist()
    formatted = set()
    for st in raw_states:
        if st.lower() == "uttrakhand":
            formatted.add("Uttarakhand")
        else:
            formatted.add(st)
    formatted.update(ALL_STATE_DISTRICTS.keys())
    return sorted(list(formatted))


@app.get("/districts/{state}")
def get_districts(state: str):
    st_clean = state.strip().lower()
    st_target = STATE_ALIASES.get(st_clean, st_clean)

    csv_dists = set()
    if not price_data.empty:
        filtered = price_data[price_data["State"].astype(str).str.strip().str.lower() == st_target]
        csv_dists = set(filtered["District"].dropna().astype(str).str.strip().unique().tolist())

    std_dists = set()
    for st_key, dist_list in ALL_STATE_DISTRICTS.items():
        if st_key.lower() == st_clean or st_key.lower() == st_target:
            std_dists.update(dist_list)

    all_dists = sorted(list(csv_dists | std_dists))
    return all_dists if all_dists else sorted(list(csv_dists))


@app.get("/markets/{state}/{district}")
def get_markets(state: str, district: str):
    st_clean = state.strip().lower()
    st_target = STATE_ALIASES.get(st_clean, st_clean)
    dist_clean = district.strip().lower()

    csv_markets = set()
    if not price_data.empty:
        filtered = price_data[
            (price_data["State"].astype(str).str.strip().str.lower() == st_target) &
            (price_data["District"].astype(str).str.strip().str.lower() == dist_clean)
        ]
        csv_markets = set(filtered["Market"].dropna().astype(str).str.strip().unique().tolist())

    dict_markets = set(DISTRICT_MARKETS.get(dist_clean, []))
    all_markets = sorted(list(csv_markets | dict_markets))

    if not all_markets:
        dist_title = district.strip().title()
        all_markets = [f"{dist_title} APMC Mandi", f"{dist_title} Main Market"]

    return all_markets


@app.get("/commodities")
def get_commodities(state: str = None, district: str = None, market: str = None):
    if price_data.empty:
        return ["Cotton", "Wheat", "Rice", "Maize", "Groundnut", "Tomato", "Onion", "Chilli"]

    filtered = price_data.copy()
    if state:
        st_target = STATE_ALIASES.get(state.strip().lower(), state.strip().lower())
        filtered = filtered[filtered["State"].astype(str).str.strip().str.lower() == st_target]
    if district:
        filtered = filtered[filtered["District"].astype(str).str.strip().str.lower() == district.strip().lower()]
    if market:
        filtered = filtered[filtered["Market"].astype(str).str.strip().str.lower() == market.strip().lower()]

    commodities = sorted(filtered["Commodity"].dropna().astype(str).str.strip().unique().tolist())
    if not commodities:
        commodities = sorted(price_data["Commodity"].dropna().astype(str).str.strip().unique().tolist())

    return commodities


def _fetch_varieties(state: str = None, district: str = None, market: str = None, commodity: str = None):
    if price_data.empty:
        return ["Standard Variety", "Hybrid", "Average (Whole)", "FAQ", "Other"]

    filtered = price_data.copy()
    if state:
        st_target = STATE_ALIASES.get(state.strip().lower(), state.strip().lower())
        filtered = filtered[filtered["State"].astype(str).str.strip().str.lower() == st_target]
    if district:
        filtered = filtered[filtered["District"].astype(str).str.strip().str.lower() == district.strip().lower()]
    if market:
        filtered = filtered[filtered["Market"].astype(str).str.strip().str.lower() == market.strip().lower()]
    if commodity:
        filtered = filtered[filtered["Commodity"].astype(str).str.strip().str.lower() == commodity.strip().lower()]

    res = sorted(filtered["Variety"].dropna().astype(str).str.strip().unique().tolist())
    if not res and commodity:
        res = sorted(
            price_data[price_data["Commodity"].astype(str).str.strip().str.lower() == commodity.strip().lower()]["Variety"]
            .dropna().astype(str).str.strip().unique().tolist()
        )
    if not res:
        res = sorted(price_data["Variety"].dropna().astype(str).str.strip().unique().tolist())
    if not res:
        res = ["Standard Variety", "Hybrid", "Average (Whole)", "FAQ", "Other"]

    return res


@app.get("/varieties")
def get_varieties_query(state: str = None, district: str = None, market: str = None, commodity: str = None):
    return _fetch_varieties(state, district, market, commodity)


@app.get("/varieties/{state}/{district}/{market}/{commodity}")
def get_varieties_path(state: str, district: str, market: str, commodity: str):
    return _fetch_varieties(state, district, market, commodity)


def _fetch_grades(state: str = None, district: str = None, market: str = None, commodity: str = None, variety: str = None):
    if price_data.empty:
        return ["FAQ", "Non-FAQ", "Medium", "Large", "Small"]

    filtered = price_data.copy()
    if state:
        st_target = STATE_ALIASES.get(state.strip().lower(), state.strip().lower())
        filtered = filtered[filtered["State"].astype(str).str.strip().str.lower() == st_target]
    if district:
        filtered = filtered[filtered["District"].astype(str).str.strip().str.lower() == district.strip().lower()]
    if market:
        filtered = filtered[filtered["Market"].astype(str).str.strip().str.lower() == market.strip().lower()]
    if commodity:
        filtered = filtered[filtered["Commodity"].astype(str).str.strip().str.lower() == commodity.strip().lower()]
    if variety:
        filtered = filtered[filtered["Variety"].astype(str).str.strip().str.lower() == variety.strip().lower()]

    res = sorted(filtered["Grade"].dropna().astype(str).str.strip().unique().tolist())
    if not res and variety:
        res = sorted(
            price_data[price_data["Variety"].astype(str).str.strip().str.lower() == variety.strip().lower()]["Grade"]
            .dropna().astype(str).str.strip().unique().tolist()
        )
    if not res:
        res = sorted(price_data["Grade"].dropna().astype(str).str.strip().unique().tolist())
    if not res:
        res = ["FAQ", "Non-FAQ", "Medium", "Large", "Small"]

    return res


@app.get("/grades")
def get_grades_query(state: str = None, district: str = None, market: str = None, commodity: str = None, variety: str = None):
    return _fetch_grades(state, district, market, commodity, variety)


@app.get("/grades/{state}/{district}/{market}/{commodity}/{variety}")
def get_grades_path(state: str, district: str, market: str, commodity: str, variety: str):
    return _fetch_grades(state, district, market, commodity, variety)


@app.get("/yield-options")
def get_yield_options():
    opts = quantum_engine.get_yield_options()
    all_states = sorted(list(set(opts.get("states", []) + list(ALL_STATE_DISTRICTS.keys()))))
    opts["states"] = all_states
    return opts


# =========================================================
# APPLICATION ENTRYPOINT (Local & Production Support)
# =========================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"Starting ASGI server on {host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=False)