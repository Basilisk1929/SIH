"""Domain vocabularies, Indian regional entities, banks, locations, and device taxonomies."""

from typing import Dict, List, Tuple

FIRST_NAMES = [
    "Aarav", "Aditi", "Ajay", "Amit", "Ananya", "Aniket", "Anjali", "Arjun", "Deepak",
    "Divya", "Gaurav", "Harish", "Ishaan", "Kavita", "Kiran", "Manoj", "Meera", "Neha",
    "Nikhil", "Pooja", "Pranav", "Priya", "Rahul", "Rajesh", "Ramesh", "Ravi", "Riya",
    "Rohan", "Rohit", "Sachin", "Sandeep", "Sangeeta", "Sanjay", "Shreya", "Sneha",
    "Suresh", "Swati", "Tarun", "Varun", "Vikas", "Vikram", "Vinod", "Yash", "Zoya",
]

LAST_NAMES = [
    "Agarwal", "Banerjee", "Bhatia", "Chauhan", "Das", "Deshmukh", "Gupta", "Iyer",
    "Jadhav", "Jain", "Joshi", "Kapoor", "Khan", "Kumar", "Mehta", "Mishra", "Mukherjee",
    "Nair", "Patel", "Pawar", "Prasad", "Rao", "Reddy", "Roy", "Saxena", "Sen", "Sharma",
    "Shinde", "Singh", "Sinha", "Trivedi", "Varma", "Verma", "Yadav",
]

SYNTHETIC_BANKS: List[Tuple[str, str, str]] = [
    ("SYNB", "State Bank of Synth", "Public Sector"),
    ("SYND", "Synth HDFC Commercial Bank", "Private Sector"),
    ("SYNI", "Synth ICICI Banking Corp", "Private Sector"),
    ("SYNA", "Synth Axis Finance Bank", "Private Sector"),
    ("SYNP", "Punjab & Synth National Bank", "Public Sector"),
    ("SYNK", "Kotak Synth Mahindra Bank", "Private Sector"),
    ("SYNM", "Bank of Synth Baroda", "Public Sector"),
    ("SYNU", "Union Synth Bank of India", "Public Sector"),
    ("SYNE", "Synth Payments & Small Finance Bank", "Payments Bank"),
    ("SYNJ", "Jan-Synth Gramin Vikas Bank", "Regional Rural"),
]

INDIAN_STATES_DATA: List[Dict[str, any]] = [
    {"state": "Maharashtra", "cities": [("Mumbai", "400001", 18.9220, 72.8347), ("Pune", "411001", 18.5204, 73.8567), ("Nagpur", "440001", 21.1458, 79.0882)]},
    {"state": "Delhi", "cities": [("New Delhi", "110001", 28.6139, 77.2090), ("Dwarka", "110075", 28.5921, 77.0460), ("Rohini", "110085", 28.7495, 77.0565)]},
    {"state": "Karnataka", "cities": [("Bengaluru", "560001", 12.9716, 77.5946), ("Mysuru", "570001", 12.2958, 76.6394), ("Hubballi", "580020", 15.3647, 75.1240)]},
    {"state": "Telangana", "cities": [("Hyderabad", "500001", 17.3850, 78.4867), ("Secunderabad", "500003", 17.4399, 78.4983), ("Warangal", "506001", 17.9689, 79.5941)]},
    {"state": "Uttar Pradesh", "cities": [("Noida", "201301", 28.5355, 77.3910), ("Lucknow", "226001", 26.8467, 80.9462), ("Kanpur", "208001", 26.4499, 80.3319)]},
    {"state": "Rajasthan", "cities": [("Jaipur", "302001", 26.9124, 75.7873), ("Jodhpur", "342001", 26.2389, 73.0243), ("Kota", "324001", 25.2138, 75.8648)]},
    {"state": "Gujarat", "cities": [("Ahmedabad", "380001", 23.0225, 72.5714), ("Surat", "395001", 21.1702, 72.8311), ("Vadodara", "390001", 22.3072, 73.1812)]},
    {"state": "West Bengal", "cities": [("Kolkata", "700001", 22.5726, 88.3639), ("Bidhannagar", "700091", 22.5804, 88.4174), ("Siliguri", "734001", 26.7271, 88.3953)]},
    {"state": "Haryana", "cities": [("Gurugram", "122001", 28.4595, 77.0266), ("Faridabad", "121001", 28.4089, 77.3178), ("Ambala", "133001", 30.3782, 76.7767)]},
    {"state": "Jharkhand", "cities": [("Ranchi", "834001", 23.3441, 85.3096), ("Jamshedpur", "831001", 22.8046, 86.2029), ("Dhanbad", "826001", 23.7957, 86.4304)]},
    {"state": "Tamil Nadu", "cities": [("Chennai", "600001", 13.0827, 80.2707), ("Coimbatore", "641001", 11.0168, 76.9558), ("Madurai", "625001", 9.9252, 78.1198)]},
    {"state": "Bihar", "cities": [("Patna", "800001", 25.5941, 85.1376), ("Gaya", "823001", 24.7914, 85.0002), ("Muzaffarpur", "842001", 26.1209, 85.3647)]},
]

CYBER_CRIME_HOTSPOTS: List[Dict[str, any]] = [
    {
        "name": "Jamtara-Karmatanr Hub",
        "state": "Jharkhand",
        "district": "Jamtara",
        "pincode": "815351",
        "lat": 23.9614,
        "lng": 86.8016,
        "primary_modus": "Bank OTP Phishing & AnyDesk Screen Share",
        "risk_weight": 0.94,
    },
    {
        "name": "Mewat-Nuh Region",
        "state": "Haryana",
        "district": "Nuh",
        "pincode": "122107",
        "lat": 28.1128,
        "lng": 77.0017,
        "primary_modus": "OLX Marketplace & Armed Vehicle Impersonation",
        "risk_weight": 0.92,
    },
    {
        "name": "Bharatpur-Deeg Belt",
        "state": "Rajasthan",
        "district": "Bharatpur",
        "pincode": "321001",
        "lat": 27.2152,
        "lng": 77.5030,
        "primary_modus": "Sextortion & Fake Job Portals",
        "risk_weight": 0.88,
    },
    {
        "name": "Alwar-Ramgarh Strip",
        "state": "Rajasthan",
        "district": "Alwar",
        "pincode": "301001",
        "lat": 27.5530,
        "lng": 76.6346,
        "primary_modus": "KYC APK & SIM Swap Fraud",
        "risk_weight": 0.85,
    },
    {
        "name": "Cyberabad Hitec Cluster",
        "state": "Telangana",
        "district": "Hyderabad",
        "pincode": "500081",
        "lat": 17.4435,
        "lng": 78.3772,
        "primary_modus": "Telegram Investment & Crypto Ponzi",
        "risk_weight": 0.80,
    },
    {
        "name": "Noida Sector-62 Call Centers",
        "state": "Uttar Pradesh",
        "district": "Gautam Buddha Nagar",
        "pincode": "201309",
        "lat": 28.6280,
        "lng": 77.3649,
        "primary_modus": "CBI/FedEx Impersonation & Digital Arrest",
        "risk_weight": 0.86,
    },
    {
        "name": "Bidhannagar Fake BPO Hub",
        "state": "West Bengal",
        "district": "North 24 Parganas",
        "pincode": "700091",
        "lat": 22.5804,
        "lng": 88.4174,
        "primary_modus": "Fake Customer Care & Tech Support Scams",
        "risk_weight": 0.84,
    },
]

UPI_HANDLES = [
    "synaxis", "synsbi", "synhdfc", "synicici", "synpaytm", "synoksbi",
    "synokaxis", "synfree", "synbaroda", "synpnb", "synkotak", "synindus",
]

DEVICE_MODELS = [
    ("Redmi Note 12 Pro", "Xiaomi", "Android 13"),
    ("Samsung Galaxy M34", "Samsung", "Android 14"),
    ("Realme Narzo 60", "Realme", "Android 13"),
    ("OnePlus Nord CE 3", "OnePlus", "Android 14"),
    ("Vivo T2x 5G", "Vivo", "Android 13"),
    ("iPhone 13", "Apple", "iOS 17.2"),
    ("iPhone 14 Pro", "Apple", "iOS 17.4"),
    ("Poco X5 5G", "Xiaomi", "Android 13"),
    ("Motorola G54", "Motorola", "Android 13"),
    ("Tecno Spark 10", "Tecno", "Android 12"),
    ("Android Virtual Emulator (Nox)", "Google Emulator", "Android 9.0"),
    ("BlueStacks Rooted Instance", "BlueStacks", "Android 10.0"),
]

TELECOM_OPERATORS = ["Jio 5G", "Airtel India", "Vodafone Idea (Vi)", "BSNL Mobile"]
OCCUPATIONS = [
    "Software Engineer", "Government Employee", "Small Business Owner", "School Teacher",
    "College Student", "Retired Pensioner", "Farmer / Agri Trader", "Private Sector Executive",
    "Healthcare Worker", "Homemaker", "Shopkeeper", "Driver / Delivery Agent",
]
INCOME_BRACKETS = ["< 3 LPA", "3 - 7 LPA", "7 - 15 LPA", "15 - 30 LPA", "> 30 LPA"]
ACCOUNT_TYPES = ["SAVINGS", "CURRENT", "JAN_DHAN", "SALARY"]
TRANSACTION_TYPES = ["TRANSFER", "CASH_IN", "CASH_OUT", "PAYMENT"]
PAYMENT_CHANNELS = ["UPI", "IMPS", "NEFT", "RTGS", "ATM"]
