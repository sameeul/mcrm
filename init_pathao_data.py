#!/usr/bin/env python3
"""
Repopulate Pathao tables (cities, zones, stores, token) without touching other data.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, PathaoCity, PathaoZone, PathaoToken, PathaoStore
from pathao_service import PathaoService

def refresh_pathao_data():
    app = create_app()

    with app.app_context():
        print("Clearing Pathao tables...")
        PathaoZone.query.delete()
        PathaoCity.query.delete()
        PathaoStore.query.delete()
        PathaoToken.query.delete()
        db.session.commit()

        print("Fetching cities...")
        PathaoService.get_cities(force_refresh=True)

        print("Fetching zones...")
        for city in PathaoCity.query.all():
            PathaoService.get_zones(force_refresh=True, city_id=city.city_id)

        print("Fetching stores...")
        PathaoService.get_stores(force_refresh=True)

        cities = PathaoCity.query.count()
        zones = PathaoZone.query.count()
        stores = PathaoStore.query.count()
        print(f"Done. {cities} cities, {zones} zones, {stores} stores.")

if __name__ == '__main__':
    refresh_pathao_data()
