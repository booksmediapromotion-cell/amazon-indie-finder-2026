"""Configuration for Amazon Indie Author Finder 2026"""
import os
from datetime import datetime, date

APP_NAME = "Amazon Indie Author Finder 2026"
APP_VERSION = "1.0.0"
MIN_PUBLICATION_YEAR = 2026
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'indie_authors.db')
DISCOVERY_INTERVAL_HOURS = 24
MAX_RESULTS_PER_SOURCE = 100
RATE_LIMIT_DELAY_SECONDS = 2
SCORE_HIGH_MIN = 80
SCORE_MEDIUM_MIN = 50

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

USA_STATES = ["All USA", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]

PUBLISHING_TYPES = ["Self-Published", "Independent", "Small Press", "Unknown / Needs Verification"]
VERIFICATION_STATUSES = ["Verified Indie", "Likely Indie", "Needs Review", "Not Indie"]

MAJOR_PUBLISHERS = ["Penguin Random House", "HarperCollins", "Simon & Schuster", "Macmillan", "Hachette"]
SELF_PUBLISH_INDICATORS = ["Independently published", "Self-published", "KDP", "Draft2Digital", "Smashwords"]
