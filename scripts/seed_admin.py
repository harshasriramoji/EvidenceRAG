"""
Seed Admin Script for EvidenceRAG Development
Usage:
    python scripts/seed_admin.py --email admin@custom.com --password YourPassword --name "Custom Admin"
"""
import argparse
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import SessionLocal, Base, engine
from backend.app.models.entities import User
from backend.app.core.security import get_password_hash
from backend.app.database.init_db import init_database

def seed_admin(email: str, password: str, full_name: str):
    init_database()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"Updating existing user '{email}' to admin role...")
            user.role = "admin"
            user.full_name = full_name
            user.hashed_password = get_password_hash(password)
        else:
            print(f"Creating new admin user '{email}'...")
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                role="admin",
                is_active=True
            )
            db.add(user)
        db.commit()
        print(f"Admin user '{email}' seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Admin User for EvidenceRAG")
    parser.add_argument("--email", default="admin@evidencerag.com", help="Admin email address")
    parser.add_argument("--password", default="Admin@12345", help="Admin password")
    parser.add_argument("--name", default="System Administrator", help="Admin full name")
    args = parser.parse_args()

    seed_admin(args.email, args.password, args.name)
