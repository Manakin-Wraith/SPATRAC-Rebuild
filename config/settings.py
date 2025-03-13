"""
Application configuration settings.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Application settings
APP_NAME = "SPATRAC"
APP_TITLE = "SPATRAC - Product Traceability Dashboard"
APP_ICON = "🏭"
APP_LAYOUT = "wide"

# Navigation structure
NAVIGATION = {
    'Overview': {
        'icon': 'house',
        'pages': ['Overview']
    },
    'Inventory Management': {
        'icon': 'box-seam',
        'pages': ['Inventory Management', 'Expired Products']
    },
    'Product Management': {
        'icon': 'tags',
        'pages': ['Products', 'Recipes & Ingredients', 'Recipe Production', 'Suppliers']
    },
    'Logistics': {
        'icon': 'truck',
        'pages': ['Deliveries', 'Traceability', 'Edit Delivery']
    },
    'Analytics & Reporting': {
        'icon': 'graph-up',
        'pages': ['Sales Analytics', 'Reports', 'Waste Analysis']
    }
}

# For backward compatibility with older code
PAGES = []
for category in NAVIGATION:
    PAGES.extend(NAVIGATION[category]['pages'])

# Data display settings
ITEMS_PER_PAGE = 50
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Product settings
TEMPERATURE_RANGES = {
    'Frozen': (-25, -15),
    'Chilled': (2, 8),
    'Ambient': (15, 25)
}

# Quality control settings
QC_STATUSES = ['PENDING', 'PASSED', 'FAILED']
DEFAULT_QC_STATUS = 'PENDING'

# Time windows
DEFAULT_HISTORY_WINDOW = timedelta(days=30)
EXPIRY_WARNING_DAYS = 30
BEST_BEFORE_WARNING_DAYS = 14

# Storage settings
STORAGE_LOCATIONS = [
    'Receiving Area',
    'Cold Storage',
    'Freezer',
    'Dry Storage',
    'Production Area'
]

# Chart settings
CHART_HEIGHT = 400
CHART_WIDTH = 800
COLOR_SCHEME = {
    'PASSED': '#2ecc71',
    'FAILED': '#e74c3c',
    'PENDING': '#f1c40f',
    'primary': '#3498db',
    'secondary': '#95a5a6',
    'background': '#ecf0f1'
}

# Network graph settings
NETWORK_LAYOUT = 'spring'
NODE_SIZE = 1000
EDGE_WIDTH = 2

# Cache settings
CACHE_TTL = 300  # seconds
MAX_CACHE_SIZE = 100  # items
