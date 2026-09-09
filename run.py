#!/usr/bin/env python3
"""Quick start script"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

print("=" * 60)
print("📚 Amazon Indie Author Finder 2026")
print("=" * 60)

db = DatabaseManager()
print(f"\n✅ Database ready")
print(f"📊 Books: {db.count_books()}")
print(f"📊 Authors: {db.count_authors()}")

print("\n" + "=" * 60)
print("🚀 Starting application...")
print("=" * 60)
print("\nOpen: http://localhost:8501\n")

os.system("streamlit run app.py")
