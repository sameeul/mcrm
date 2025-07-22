#!/usr/bin/env python3
"""
Enhanced Database Initialization Script
Creates all tables and populates with sample data including Pathao integration
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, PathaoCity
from pathao_service import PathaoService

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        print("🗄️  Dropping existing tables...")
        db.drop_all()
        
        print("🏗️  Creating new tables...")
        db.create_all()
        
        print("👤 Creating users...")
        create_users()
        

        
        print("🌍 Creating Pathao data...")
        create_pathao_data()
        
        print("✅ Database initialization completed successfully!")
        print("\n🔑 Login credentials:")
        print("   Admin: admin / admin123")
        print("   User:  user / user123")

def create_users():
    """Create sample users"""
    # Admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        role='admin'
    )
    admin.set_password('admin123')
    admin.last_login = datetime.utcnow()
    db.session.add(admin)
    
    db.session.commit()


def create_pathao_data():
    """Create Pathao cities and zones"""
    print("Fetching Pathao Cities")
    PathaoService.get_cities(force_refresh = True)
    # for each PathaoCity, retrieve PathaoZoneS
    print("Fetching Pathao Zones")
    for city in PathaoCity.query.all():
        PathaoService.get_zones(force_refresh = True, city_id = city.id)
    print("Fetching Pathao Stores")
    PathaoService.get_stores(force_refresh = True)

if __name__ == '__main__':
    init_database()
