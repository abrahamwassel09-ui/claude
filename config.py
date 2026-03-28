"""
Configuration for the AI Content Automation System.
Edit the paths and model descriptions here.
"""

import os

# --- PATHS ---
# Folder where Higgsfield exports land (the system watches this folder)
WATCH_FOLDER = r"C:\Higgsfield_Exports"

# Root folder where sorted content goes
CONTENT_ROOT = r"C:\Content"

# Database file (SQLite) — stored next to the scripts
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content_tracker.db")

# Log file
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "organizer.log")

# --- SCHEDULE ---
DAYS = ["Thursday", "Friday", "Saturday", "Sunday"]
POSTS_PER_DAY = 3  # Post1, Post2, Post3 — adjust if you need more

# --- MODEL PROFILES ---
# These descriptions are sent to Claude Vision for identification
MODELS = {
    "Savannah": {
        "full_name": "Savannah Hayes",
        "description": (
            "Savannah Hayes: platinum blonde curly hair, blue-green eyes, "
            "light skin with a warm golden tan, light freckles across her face."
        ),
    },
    "Keliah": {
        "full_name": "Keliah Rose",
        "description": (
            "Keliah Rose: long dark brown curly hair with caramel highlights, "
            "warm medium-deep brown skin, prominent freckles, full curves."
        ),
    },
}

# --- IMAGE EXTENSIONS ---
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

# --- FLASK DASHBOARD ---
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 5000
