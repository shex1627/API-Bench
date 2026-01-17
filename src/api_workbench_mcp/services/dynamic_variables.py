"""
Dynamic Variables Service.

Provides Postman-compatible dynamic variables that generate values at runtime.
Variables are prefixed with $ and generate new values on each substitution.

Example: {{$timestamp}}, {{$guid}}, {{$randomEmail}}
"""

import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable


# Data for random generation
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Emma",
    "Oliver", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia",
    "Harper", "Evelyn", "Liam", "Noah", "Ethan", "Lucas", "Mason", "Logan",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
]

COLORS = [
    "red", "blue", "green", "yellow", "purple", "orange", "pink", "brown",
    "black", "white", "gray", "cyan", "magenta", "lime", "navy", "teal",
    "maroon", "olive", "aqua", "silver", "fuchsia", "indigo", "violet",
]

DOMAINS = [
    "example.com", "test.com", "demo.org", "sample.net", "mock.io",
    "fake.dev", "testing.co", "dummy.app",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "London", "Paris", "Tokyo", "Sydney", "Toronto", "Berlin", "Amsterdam",
    "Singapore", "Dubai", "Mumbai", "Shanghai", "Seoul", "Bangkok", "Madrid",
]

COUNTRIES = [
    ("United States", "US"), ("United Kingdom", "GB"), ("Canada", "CA"),
    ("Australia", "AU"), ("Germany", "DE"), ("France", "FR"), ("Japan", "JP"),
    ("China", "CN"), ("India", "IN"), ("Brazil", "BR"), ("Mexico", "MX"),
    ("Spain", "ES"), ("Italy", "IT"), ("Netherlands", "NL"), ("Sweden", "SE"),
    ("Singapore", "SG"), ("South Korea", "KR"), ("Switzerland", "CH"),
]

STREET_NAMES = [
    "Main", "Oak", "Maple", "Cedar", "Pine", "Elm", "Washington", "Lake",
    "Hill", "Park", "View", "Forest", "River", "Spring", "Valley", "Highland",
]

STREET_TYPES = ["St", "Ave", "Blvd", "Rd", "Dr", "Ln", "Way", "Ct", "Pl"]

JOB_TITLES = [
    "Software Engineer", "Product Manager", "Data Scientist", "Designer",
    "Marketing Manager", "Sales Representative", "Project Manager",
    "Business Analyst", "DevOps Engineer", "Quality Assurance Engineer",
    "Technical Writer", "Customer Success Manager", "Account Executive",
    "Full Stack Developer", "Frontend Developer", "Backend Developer",
]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "Finance", "Human Resources",
    "Operations", "Customer Support", "Product", "Design", "Legal",
    "Research", "IT", "Quality Assurance", "Business Development",
]

COMPANY_SUFFIXES = ["Inc", "LLC", "Corp", "Ltd", "Co", "Group", "Solutions"]

COMPANY_NAMES = [
    "Tech", "Global", "Dynamic", "Innovative", "Creative", "Digital",
    "Smart", "Prime", "Elite", "Pro", "Advanced", "Next", "Future",
    "Cloud", "Data", "Cyber", "Net", "Web", "App", "Soft",
]

CURRENCIES = [
    ("USD", "US Dollar", "$"), ("EUR", "Euro", "€"), ("GBP", "British Pound", "£"),
    ("JPY", "Japanese Yen", "¥"), ("AUD", "Australian Dollar", "A$"),
    ("CAD", "Canadian Dollar", "C$"), ("CHF", "Swiss Franc", "CHF"),
    ("CNY", "Chinese Yuan", "¥"), ("INR", "Indian Rupee", "₹"),
]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

FILE_EXTENSIONS = ["txt", "pdf", "doc", "docx", "xls", "xlsx", "csv", "json", "xml", "html"]
MIME_TYPES = [
    "application/json", "application/xml", "text/plain", "text/html",
    "application/pdf", "image/png", "image/jpeg", "application/octet-stream",
]

LOREM_WORDS = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing",
    "elit", "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore",
    "et", "dolore", "magna", "aliqua", "enim", "ad", "minim", "veniam",
    "quis", "nostrud", "exercitation", "ullamco", "laboris", "nisi",
    "aliquip", "ex", "ea", "commodo", "consequat", "duis", "aute", "irure",
    "in", "reprehenderit", "voluptate", "velit", "esse", "cillum", "fugiat",
    "nulla", "pariatur", "excepteur", "sint", "occaecat", "cupidatat",
    "non", "proident", "sunt", "culpa", "qui", "officia", "deserunt",
    "mollit", "anim", "id", "est", "laborum",
]


# =========================================================================
# Generator Functions
# =========================================================================

def _guid() -> str:
    """Generate a UUID v4."""
    return str(uuid.uuid4())


def _timestamp() -> str:
    """Current UNIX timestamp in seconds."""
    return str(int(datetime.now(timezone.utc).timestamp()))


def _iso_timestamp() -> str:
    """Current ISO 8601 timestamp in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _random_int() -> str:
    """Random integer between 0 and 1000."""
    return str(random.randint(0, 1000))


def _random_boolean() -> str:
    """Random boolean value."""
    return str(random.choice([True, False])).lower()


def _random_alphanumeric() -> str:
    """Single random alphanumeric character."""
    return random.choice(string.ascii_letters + string.digits)


def _random_hex_color() -> str:
    """Random hex color code."""
    return f"#{random.randint(0, 0xFFFFFF):06x}"


def _random_color() -> str:
    """Random color name."""
    return random.choice(COLORS)


def _random_first_name() -> str:
    """Random first name."""
    return random.choice(FIRST_NAMES)


def _random_last_name() -> str:
    """Random last name."""
    return random.choice(LAST_NAMES)


def _random_full_name() -> str:
    """Random full name."""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _random_email() -> str:
    """Random email address."""
    first = random.choice(FIRST_NAMES).lower()
    last = random.choice(LAST_NAMES).lower()
    num = random.randint(1, 999)
    domain = random.choice(DOMAINS)
    return f"{first}.{last}{num}@{domain}"


def _random_username() -> str:
    """Random username."""
    first = random.choice(FIRST_NAMES).lower()
    num = random.randint(1, 9999)
    return f"{first}{num}"


def _random_password() -> str:
    """Random 15-character alphanumeric password."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(15))


def _random_url() -> str:
    """Random URL."""
    domain = random.choice(DOMAINS)
    path = random.choice(["api", "v1", "users", "products", "data", "items"])
    return f"https://{domain}/{path}"


def _random_domain_name() -> str:
    """Random domain name."""
    return random.choice(DOMAINS)


def _random_ip() -> str:
    """Random IPv4 address."""
    return ".".join(str(random.randint(1, 255)) for _ in range(4))


def _random_ipv6() -> str:
    """Random IPv6 address."""
    return ":".join(f"{random.randint(0, 0xFFFF):04x}" for _ in range(8))


def _random_phone_number() -> str:
    """Random 10-digit phone number."""
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"{area}-{prefix}-{line}"


def _random_mac_address() -> str:
    """Random MAC address."""
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))


def _random_city() -> str:
    """Random city name."""
    return random.choice(CITIES)


def _random_country() -> str:
    """Random country name."""
    return random.choice(COUNTRIES)[0]


def _random_country_code() -> str:
    """Random ISO 3166-1 alpha-2 country code."""
    return random.choice(COUNTRIES)[1]


def _random_street_address() -> str:
    """Random street address."""
    num = random.randint(1, 9999)
    street = random.choice(STREET_NAMES)
    street_type = random.choice(STREET_TYPES)
    return f"{num} {street} {street_type}"


def _random_latitude() -> str:
    """Random latitude coordinate."""
    return f"{random.uniform(-90, 90):.6f}"


def _random_longitude() -> str:
    """Random longitude coordinate."""
    return f"{random.uniform(-180, 180):.6f}"


def _random_company_name() -> str:
    """Random company name."""
    name = random.choice(COMPANY_NAMES)
    suffix = random.choice(COMPANY_SUFFIXES)
    return f"{name} {suffix}"


def _random_job_title() -> str:
    """Random job title."""
    return random.choice(JOB_TITLES)


def _random_department() -> str:
    """Random department name."""
    return random.choice(DEPARTMENTS)


def _random_price() -> str:
    """Random price between 0 and 1000."""
    return f"{random.uniform(0, 1000):.2f}"


def _random_currency_code() -> str:
    """Random ISO 4217 currency code."""
    return random.choice(CURRENCIES)[0]


def _random_currency_name() -> str:
    """Random currency name."""
    return random.choice(CURRENCIES)[1]


def _random_currency_symbol() -> str:
    """Random currency symbol."""
    return random.choice(CURRENCIES)[2]


def _random_bank_account() -> str:
    """Random 8-digit bank account number."""
    return "".join(str(random.randint(0, 9)) for _ in range(8))


def _random_date_past() -> str:
    """Random date in the past year."""
    days_ago = random.randint(1, 365)
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _random_date_future() -> str:
    """Random date in the next year."""
    days_ahead = random.randint(1, 365)
    dt = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _random_date_recent() -> str:
    """Random date in the past week."""
    days_ago = random.randint(0, 7)
    hours_ago = random.randint(0, 23)
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _random_weekday() -> str:
    """Random day of the week."""
    return random.choice(WEEKDAYS)


def _random_month() -> str:
    """Random month name."""
    return random.choice(MONTHS)


def _random_file_name() -> str:
    """Random filename with extension."""
    name = random.choice(LOREM_WORDS)
    ext = random.choice(FILE_EXTENSIONS)
    return f"{name}.{ext}"


def _random_file_ext() -> str:
    """Random file extension."""
    return random.choice(FILE_EXTENSIONS)


def _random_mime_type() -> str:
    """Random MIME type."""
    return random.choice(MIME_TYPES)


def _random_word() -> str:
    """Random word."""
    return random.choice(LOREM_WORDS)


def _random_words() -> str:
    """Random 3-5 words."""
    count = random.randint(3, 5)
    return " ".join(random.choice(LOREM_WORDS) for _ in range(count))


def _random_lorem_word() -> str:
    """Single lorem ipsum word."""
    return random.choice(LOREM_WORDS)


def _random_lorem_words() -> str:
    """Multiple lorem ipsum words (3-7)."""
    count = random.randint(3, 7)
    return " ".join(random.choice(LOREM_WORDS) for _ in range(count))


def _random_lorem_sentence() -> str:
    """Lorem ipsum sentence."""
    count = random.randint(5, 12)
    words = [random.choice(LOREM_WORDS) for _ in range(count)]
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def _random_lorem_paragraph() -> str:
    """Lorem ipsum paragraph (3-5 sentences)."""
    sentences = []
    for _ in range(random.randint(3, 5)):
        count = random.randint(5, 12)
        words = [random.choice(LOREM_WORDS) for _ in range(count)]
        words[0] = words[0].capitalize()
        sentences.append(" ".join(words) + ".")
    return " ".join(sentences)


# =========================================================================
# Variable Registry
# =========================================================================

VARIABLE_GENERATORS: dict[str, Callable[[], str]] = {
    # Core
    "$guid": _guid,
    "$randomUUID": _guid,
    "$timestamp": _timestamp,
    "$isoTimestamp": _iso_timestamp,
    "$randomInt": _random_int,
    "$randomBoolean": _random_boolean,
    # Text & Numbers
    "$randomAlphaNumeric": _random_alphanumeric,
    "$randomHexColor": _random_hex_color,
    "$randomColor": _random_color,
    # Names
    "$randomFirstName": _random_first_name,
    "$randomLastName": _random_last_name,
    "$randomFullName": _random_full_name,
    # Internet & Contact
    "$randomEmail": _random_email,
    "$randomUserName": _random_username,
    "$randomPassword": _random_password,
    "$randomUrl": _random_url,
    "$randomDomainName": _random_domain_name,
    "$randomIP": _random_ip,
    "$randomIPV6": _random_ipv6,
    "$randomPhoneNumber": _random_phone_number,
    "$randomMACAddress": _random_mac_address,
    # Location
    "$randomCity": _random_city,
    "$randomCountry": _random_country,
    "$randomCountryCode": _random_country_code,
    "$randomStreetAddress": _random_street_address,
    "$randomLatitude": _random_latitude,
    "$randomLongitude": _random_longitude,
    # Business
    "$randomCompanyName": _random_company_name,
    "$randomJobTitle": _random_job_title,
    "$randomDepartment": _random_department,
    # Financial
    "$randomPrice": _random_price,
    "$randomCurrencyCode": _random_currency_code,
    "$randomCurrencyName": _random_currency_name,
    "$randomCurrencySymbol": _random_currency_symbol,
    "$randomBankAccount": _random_bank_account,
    # Dates
    "$randomDatePast": _random_date_past,
    "$randomDateFuture": _random_date_future,
    "$randomDateRecent": _random_date_recent,
    "$randomWeekday": _random_weekday,
    "$randomMonth": _random_month,
    # Files & Content
    "$randomFileName": _random_file_name,
    "$randomFileExt": _random_file_ext,
    "$randomMimeType": _random_mime_type,
    "$randomWord": _random_word,
    "$randomWords": _random_words,
    "$randomLoremWord": _random_lorem_word,
    "$randomLoremWords": _random_lorem_words,
    "$randomLoremSentence": _random_lorem_sentence,
    "$randomLoremParagraph": _random_lorem_paragraph,
}


class DynamicVariables:
    """
    Generates dynamic variable values at runtime.

    Supports Postman-compatible variable names prefixed with $.
    """

    # Expose data lists for testing
    FIRST_NAMES = FIRST_NAMES
    LAST_NAMES = LAST_NAMES
    COLORS = COLORS
    DOMAINS = DOMAINS
    CITIES = CITIES
    COUNTRIES = COUNTRIES
    STREET_NAMES = STREET_NAMES
    STREET_TYPES = STREET_TYPES
    JOB_TITLES = JOB_TITLES
    DEPARTMENTS = DEPARTMENTS
    COMPANY_SUFFIXES = COMPANY_SUFFIXES
    COMPANY_NAMES = COMPANY_NAMES
    CURRENCIES = CURRENCIES
    WEEKDAYS = WEEKDAYS
    MONTHS = MONTHS
    FILE_EXTENSIONS = FILE_EXTENSIONS
    MIME_TYPES = MIME_TYPES
    LOREM_WORDS = LOREM_WORDS

    @classmethod
    def is_dynamic_variable(cls, name: str) -> bool:
        """Check if a variable name is a dynamic variable (starts with $)."""
        return name.startswith("$") and name in VARIABLE_GENERATORS

    @classmethod
    def get_value(cls, name: str) -> str | None:
        """Get the generated value for a dynamic variable."""
        generator = VARIABLE_GENERATORS.get(name)
        if generator:
            return generator()
        return None

    @classmethod
    def list_variables(cls) -> list[str]:
        """List all available dynamic variables."""
        return sorted(VARIABLE_GENERATORS.keys())
