import csv
from pathlib import Path
from difflib import get_close_matches


# ---------------------------------------------------------
# Pricing file location
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
PRICING_FILE = BASE_DIR / "data" / "pricing.csv"


# ---------------------------------------------------------
# Service aliases
# ---------------------------------------------------------

SERVICE_ALIASES = {
    "website": "Website Development",
    "websites": "Website Development",
    "website development": "Website Development",
    "website development package": "Website Development",
    "website development packages": "Website Development",
    "web development": "Website Development",
    "web development package": "Website Development",
    "web development packages": "Website Development",

    "maintenance": "Website Maintenance",
    "website maintenance": "Website Maintenance",
    "website maintenance service": "Website Maintenance",

    "ui ux": "UI UX Design",
    "ui/ux": "UI UX Design",
    "ui ux design": "UI UX Design",
    "ui/ux design": "UI UX Design",

    "seo": "SEO Optimization",
    "seo service": "SEO Optimization",
    "seo services": "SEO Optimization",

    "mobile app": "Mobile App Development",
    "mobile application": "Mobile App Development",
    "mobile app development": "Mobile App Development",

    "data analytics": "Data Analytics",
    "data analysis": "Data Analytics",

    "ai chatbot": "AI Chatbot Development",
    "chatbot": "AI Chatbot Development",
    "ai chatbot development": "AI Chatbot Development",

    "social media": "Social Media Management",
    "social media management": "Social Media Management",

    "digital marketing": "Digital Marketing",
}


# ---------------------------------------------------------
# Normalize text
# ---------------------------------------------------------

def normalize_service_name(service_name):
    """
    Converts service names into a standard format
    for reliable matching.
    """

    if not service_name:
        return ""

    service_name = str(service_name).strip().lower()

    # Remove extra spaces
    service_name = " ".join(service_name.split())

    return service_name


# ---------------------------------------------------------
# Load pricing database
# ---------------------------------------------------------

def load_pricing_data():
    """
    Loads service prices from pricing.csv.

    Expected CSV columns:
        Service, Price

    Example:
        Website Development,15000
        Website Maintenance,3000
    """

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

                service = (
                    row.get("Service")
                    or row.get("service")
                    or row.get("SERVICE")
                )

                price = (
                    row.get("Price")
                    or row.get("price")
                    or row.get("PRICE")
                )

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


# ---------------------------------------------------------
# Get pricing source
# ---------------------------------------------------------

def get_pricing_source():
    """
    Returns the current pricing data source.
    """

    return "Local CSV Pricing Database"


# ---------------------------------------------------------
# Find service price
# ---------------------------------------------------------

def find_service_price(service_name):
    """
    Finds a service price using:

    1. Exact match
    2. Alias match
    3. Fuzzy match

    IMPORTANT:
    The function NEVER creates or estimates a price.

    If the service cannot be found in the pricing database,
    price_found will be False.
    """

    pricing_data = load_pricing_data()

    if not pricing_data:
        return {
            "found": False,
            "price": None,
            "matched_service": None,
            "match_type": "Not Found",
            "source": get_pricing_source()
        }

    original_name = str(service_name).strip()
    normalized_name = normalize_service_name(original_name)

    # -----------------------------------------------------
    # 1. Exact match
    # -----------------------------------------------------

    for service, price in pricing_data.items():

        if normalize_service_name(service) == normalized_name:

            return {
                "found": True,
                "price": price,
                "matched_service": service,
                "match_type": "Exact Match",
                "source": get_pricing_source()
            }

    # -----------------------------------------------------
    # 2. Alias match
    # -----------------------------------------------------

    alias_target = SERVICE_ALIASES.get(normalized_name)

    if alias_target:

        for service, price in pricing_data.items():

            if normalize_service_name(service) == normalize_service_name(
                alias_target
            ):

                return {
                    "found": True,
                    "price": price,
                    "matched_service": service,
                    "match_type": "Alias Match",
                    "source": get_pricing_source()
                }

    # -----------------------------------------------------
    # 3. Fuzzy match
    # -----------------------------------------------------

    normalized_services = {
        normalize_service_name(service): service
        for service in pricing_data.keys()
    }

    possible_matches = get_close_matches(
        normalized_name,
        normalized_services.keys(),
        n=1,
        cutoff=0.75
    )

    if possible_matches:

        matched_normalized = possible_matches[0]
        matched_service = normalized_services[matched_normalized]
        matched_price = pricing_data[matched_service]

        return {
            "found": True,
            "price": matched_price,
            "matched_service": matched_service,
            "match_type": "Fuzzy Match",
            "source": get_pricing_source()
        }

    # -----------------------------------------------------
    # 4. Not found
    # -----------------------------------------------------

    return {
        "found": False,
        "price": None,
        "matched_service": None,
        "match_type": "Not Found",
        "source": get_pricing_source()
    }


# ---------------------------------------------------------
# Get all available services
# ---------------------------------------------------------

def get_available_services():
    """
    Returns all services available in the pricing database.
    """

    pricing_data = load_pricing_data()

    return list(pricing_data.keys())