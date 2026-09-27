import csv
from pathlib import Path
from difflib import get_close_matches


# =========================================================
# PRICING FILE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Your actual file
PRICING_FILE = BASE_DIR / "data" / "services.csv"


# =========================================================
# SERVICE ALIASES
# =========================================================

SERVICE_ALIASES = {
    # Website Development
    "website": "website development",
    "websites": "website development",
    "website development": "website development",
    "website development package": "website development",
    "website development packages": "website development",
    "web development": "website development",
    "web development package": "website development",
    "web development packages": "website development",

    # Website Maintenance
    "maintenance": "website maintenance",
    "website maintenance": "website maintenance",
    "website maintenance service": "website maintenance",
    "website maintenance services": "website maintenance",

    # UI UX
    "ui ux": "ui ux design",
    "ui/ux": "ui ux design",
    "ui ux design": "ui ux design",
    "ui/ux design": "ui ux design",
    "ui design": "ui ux design",
    "ux design": "ui ux design",

    # SEO
    "seo": "seo optimization",
    "seo service": "seo optimization",
    "seo services": "seo optimization",
    "seo optimization": "seo optimization",

    # Mobile App
    "mobile app": "mobile app development",
    "mobile application": "mobile app development",
    "mobile app development": "mobile app development",
    "mobile application development": "mobile app development",

    # Cloud
    "cloud hosting": "cloud hosting",
    "cloud hosting service": "cloud hosting",

    # Data Analytics
    "data analytics": "data analytics",
    "data analysis": "data analytics",
    "data analytics service": "data analytics",
    "data analytics services": "data analytics",
    "data analyst": "data analytics",

    # AI Chatbot
    "chatbot": "ai chatbot development",
    "ai chatbot": "ai chatbot development",
    "ai chatbot development": "ai chatbot development",
    "ai chatbot service": "ai chatbot development",

    # Social Media
    "social media": "social media management",
    "social media management": "social media management",
    "social media management service": "social media management",
    "social media management services": "social media management",

    # Digital Marketing
    "digital marketing": "digital marketing",
    "digital marketing service": "digital marketing",
    "digital marketing services": "digital marketing",
}


# =========================================================
# NORMALIZE SERVICE NAME
# =========================================================

def normalize_service_name(service_name):

    if not service_name:
        return ""

    name = str(service_name).strip().lower()

    # Make separators consistent
    name = name.replace("/", " ")
    name = name.replace("-", " ")
    name = name.replace("_", " ")

    # Remove punctuation
    for char in [".", ",", ":", ";", "(", ")", "[", "]"]:
        name = name.replace(char, " ")

    # Remove common extra words
    removable_words = {
        "package",
        "packages",
        "service",
        "services",
    }

    words = name.split()

    words = [
        word
        for word in words
        if word not in removable_words
    ]

    return " ".join(words)


# =========================================================
# CANONICAL SERVICE NAME
# =========================================================

def get_canonical_service_name(service_name):

    normalized = normalize_service_name(service_name)

    return SERVICE_ALIASES.get(
        normalized,
        normalized
    )


# =========================================================
# LOAD SERVICE DATABASE
# =========================================================

def load_pricing_data():

    if not PRICING_FILE.exists():
        return {}

    pricing_data = {}

    try:

        with open(
            PRICING_FILE,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                # Your actual CSV column
                service = row.get("service_name")

                # Your actual CSV column
                price = row.get("unit_price")

                if not service or price is None:
                    continue

                service = str(service).strip()

                try:

                    price = float(
                        str(price)
                        .replace("₹", "")
                        .replace(",", "")
                        .strip()
                    )

                except ValueError:

                    continue

                pricing_data[service] = price

    except Exception:

        return {}

    return pricing_data


# =========================================================
# PRICING SOURCE
# =========================================================

def get_pricing_source():

    return "Local CSV Service Database"


# =========================================================
# FIND SERVICE PRICE
# =========================================================

def find_service_price(service_name):

    pricing_data = load_pricing_data()

    # CSV could not be loaded
    if not pricing_data:

        return {
            "found": False,
            "price": None,
            "matched_service": None,
            "match_type": "Not Found",
            "source": get_pricing_source()
        }

    original_name = str(service_name).strip()

    normalized_input = normalize_service_name(
        original_name
    )

    canonical_input = get_canonical_service_name(
        original_name
    )

    # =====================================================
    # 1. EXACT MATCH
    # =====================================================

    for service, price in pricing_data.items():

        normalized_database = normalize_service_name(
            service
        )

        if normalized_database == normalized_input:

            return {
                "found": True,
                "price": price,
                "matched_service": service,
                "match_type": "Exact Match",
                "source": get_pricing_source()
            }

    # =====================================================
    # 2. ALIAS / CANONICAL MATCH
    # =====================================================

    for service, price in pricing_data.items():

        canonical_database = get_canonical_service_name(
            service
        )

        if canonical_database == canonical_input:

            return {
                "found": True,
                "price": price,
                "matched_service": service,
                "match_type": "Alias Match",
                "source": get_pricing_source()
            }

    # =====================================================
    # 3. FUZZY MATCH
    # =====================================================

    normalized_services = {}

    for service in pricing_data.keys():

        normalized = normalize_service_name(
            service
        )

        normalized_services[normalized] = service

    possible_matches = get_close_matches(
        normalized_input,
        normalized_services.keys(),
        n=1,
        cutoff=0.70
    )

    if possible_matches:

        matched_normalized = possible_matches[0]

        matched_service = normalized_services[
            matched_normalized
        ]

        matched_price = pricing_data[
            matched_service
        ]

        return {
            "found": True,
            "price": matched_price,
            "matched_service": matched_service,
            "match_type": "Fuzzy Match",
            "source": get_pricing_source()
        }

    # =====================================================
    # 4. NOT FOUND
    # =====================================================

    return {
        "found": False,
        "price": None,
        "matched_service": None,
        "match_type": "Not Found",
        "source": get_pricing_source()
    }


# =========================================================
# GET AVAILABLE SERVICES
# =========================================================

def get_available_services():

    pricing_data = load_pricing_data()

    return list(pricing_data.keys())