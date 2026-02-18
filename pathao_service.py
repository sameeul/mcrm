import requests
import json
from datetime import datetime, timedelta, UTC
from models import db, PathaoCity, PathaoZone, PathaoToken, PathaoStore
from flask import current_app

class PathaoService:
    CACHE_DURATION_HOURS = 24  # Cache location data for 24 hours
    
    @staticmethod
    def get_config():
        cfg = current_app.config
        return {
            "BASE_URL": cfg["PATHAO_BASE_URL"],
            "CLIENT_ID": cfg["PATHAO_CLIENT_ID"],
            "CLIENT_SECRET": cfg["PATHAO_CLIENT_SECRET"],
            "USERNAME": cfg["PATHAO_USERNAME"],
            "PASSWORD": cfg["PATHAO_PASSWORD"],
            "GRANT_TYPE": cfg["PATHAO_GRANT_TYPE"],
        }

    @classmethod
    def get_access_token(cls):
        """Get valid access token, refresh if needed"""
        try:
            # Check if we have a valid token in database
            token_record = PathaoToken.query.first()
            
            if token_record and not token_record.is_expired:
                return token_record.access_token
            
            # Need to get new token
            if token_record and token_record.refresh_token:
                # Try to refresh existing token
                new_token = cls._refresh_token(token_record.refresh_token)
                if new_token:
                    return new_token
            
            # Get completely new token
            return cls._issue_new_token()
            
        except Exception as e:
            current_app.logger.error(f"Error getting access token: {str(e)}")
            return None
    
    @classmethod
    def _issue_new_token(cls):
        """Issue a new access token"""
        try:
            config = cls.get_config()
            url = f"{config['BASE_URL']}/aladdin/api/v1/issue-token"
            payload = {
                "client_id": config["CLIENT_ID"],
                "client_secret": config["CLIENT_SECRET"],
                "grant_type": config["GRANT_TYPE"],
                "username": config["USERNAME"],
                "password": config["PASSWORD"]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate expiry time (subtract 1 hour for safety)
            expires_in = data.get('expires_in', 432000)  # Default 5 days
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in - 3600)
            
            # Save token to database
            token_record = PathaoToken.query.first()
            if token_record:
                token_record.access_token = data['access_token']
                token_record.refresh_token = data['refresh_token']
                token_record.expires_at = expires_at
            else:
                token_record = PathaoToken(
                    access_token=data['access_token'],
                    refresh_token=data['refresh_token'],
                    expires_at=expires_at
                )
                db.session.add(token_record)
            
            db.session.commit()
            return data['access_token']
            
        except Exception as e:
            current_app.logger.error(f"Error issuing new token: {str(e)}")
            return None
    
    @classmethod
    def _refresh_token(cls, refresh_token):
        """Refresh access token using refresh token"""
        try:
            config = cls.get_config()
            url = f"{config['BASE_URL']}/aladdin/api/v1/issue-token"
            payload = {
                "client_id": config["CLIENT_ID"],
                "client_secret": config["CLIENT_SECRET"],
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate expiry time
            expires_in = data.get('expires_in', 432000)
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in - 3600)
            
            # Update token in database
            token_record = PathaoToken.query.first()
            if token_record:
                token_record.access_token = data['access_token']
                token_record.refresh_token = data['refresh_token']
                token_record.expires_at = expires_at
                db.session.commit()
            
            return data['access_token']
            
        except Exception as e:
            current_app.logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    @classmethod
    def get_cities(cls, force_refresh=False):
        """Get list of cities with caching"""
        try:
            # Check cache first
            if not force_refresh:
                cache_cutoff = datetime.now(UTC) - timedelta(hours=cls.CACHE_DURATION_HOURS)
                cached_cities = PathaoCity.query.filter(
                    PathaoCity.last_updated > cache_cutoff
                ).all()
                
                if cached_cities:
                    return cached_cities
            
            # Fetch from API
            access_token = cls.get_access_token()
            if not access_token:
                return []
            
            config = cls.get_config()
            url = f"{config['BASE_URL']}/aladdin/api/v1/city-list"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            cities_data = data.get('data', {}).get('data', [])
            
            # Update cache
            cls._update_cities_cache(cities_data)
            
            # Return updated cache
            return PathaoCity.query.all()
            
        except Exception as e:
            current_app.logger.error(f"Error fetching cities: {str(e)}")
            # Return cached data even if stale
            return PathaoCity.query.all()
    
    @classmethod
    def parse_address(cls, address):
        # send a request to api/v1/address-parser as a string and get back the response
        try:
            access_token = cls.get_access_token()
            if not access_token:
                return {}
            
            config = cls.get_config()
            url = f"{config['BASE_URL']}/aladdin/api/v1/address-parser"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            payload = {"address": address}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
            
        except Exception as e:
            current_app.logger.error(f"Error parsing address: {str(e)}")
            return {}


    @classmethod
    def get_zones(cls, city_id, force_refresh=False):
        """Get zones for a city with caching"""
        try:
            # Check cache first
            if not force_refresh:
                cache_cutoff = datetime.now(UTC) - timedelta(hours=cls.CACHE_DURATION_HOURS)
                cached_zones = PathaoZone.query.filter(
                    PathaoZone.city_id == city_id,
                    PathaoZone.last_updated > cache_cutoff
                ).all()
                
                if cached_zones:
                    return cached_zones
            
            # Fetch from API
            access_token = cls.get_access_token()
            if not access_token:
                return []
            
            config = cls.get_config()
            url = f"{config['BASE_URL']}/aladdin/api/v1/cities/{city_id}/zone-list"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            zones_data = data.get('data', {}).get('data', [])
            
            # Update cache
            cls._update_zones_cache(city_id, zones_data)
            
            # Return updated cache
            return PathaoZone.query.filter_by(city_id=city_id).all()
            
        except Exception as e:
            current_app.logger.error(f"Error fetching zones for city {city_id}: {str(e)}")
            # Return cached data even if stale
            return PathaoZone.query.filter_by(city_id=city_id).all()
    
    
    @classmethod
    def _update_cities_cache(cls, cities_data):
        """Update cities cache in database"""
        try:
            for city_data in cities_data:
                city = PathaoCity.query.filter_by(city_id=city_data['city_id']).first()
                if city:
                    city.city_name = city_data['city_name']
                    city.last_updated = datetime.now(UTC)
                else:
                    city = PathaoCity(
                        city_id=city_data['city_id'],
                        city_name=city_data['city_name'],
                        last_updated=datetime.now(UTC)
                    )
                    db.session.add(city)
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating cities cache: {str(e)}")
            db.session.rollback()
    
    @classmethod
    def _update_zones_cache(cls, city_id, zones_data):
        """Update zones cache in database"""
        try:
            for zone_data in zones_data:
                zone = PathaoZone.query.filter_by(zone_id=zone_data['zone_id']).first()
                if zone:
                    zone.zone_name = zone_data['zone_name']
                    zone.city_id = city_id
                    zone.last_updated = datetime.now(UTC)
                else:
                    zone = PathaoZone(
                        zone_id=zone_data['zone_id'],
                        zone_name=zone_data['zone_name'],
                        city_id=city_id,
                        last_updated=datetime.now(UTC)
                    )
                    db.session.add(zone)
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating zones cache: {str(e)}")
            db.session.rollback()
    
    
    @classmethod
    def get_location_names(cls, city_id=None, zone_id=None):
        """Get location names for given IDs"""
        result = {}
        
        if city_id:
            city = PathaoCity.query.filter_by(city_id=city_id).first()
            result['city_name'] = city.city_name if city else None
        
        if zone_id:
            zone = PathaoZone.query.filter_by(zone_id=zone_id).first()
            result['zone_name'] = zone.zone_name if zone else None
        
        return result



    @classmethod
    def get_stores(cls, force_refresh=False):
        """Get list of stores with caching"""
        try:
            # Check cache first
            if not force_refresh:
                cache_cutoff = datetime.now(UTC) - timedelta(hours=cls.CACHE_DURATION_HOURS)
                cached_stores = PathaoStore.query.filter(PathaoStore.updated_at > cache_cutoff).all()
                if cached_stores:
                    return cached_stores

            # Fetch from API
            access_token = cls.get_access_token()
            if not access_token:
                return []

            config = cls.get_config()
            url = f"{config['BASE_URL']}/aladdin/api/v1/stores"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            stores_data = data.get('data', {}).get('data', [])

            # Update cache
            cls._update_stores_cache(stores_data)

            # Return updated cache
            return PathaoStore.query.all()

        except Exception as e:
            current_app.logger.error(f"Error fetching stores: {str(e)}")
            # Return stale cache if error occurs
            return PathaoStore.query.all()

    @classmethod
    def _update_stores_cache(cls, stores_data):
        """Update stores cache in database"""
        try:
            for store_data in stores_data:
                store = PathaoStore.query.filter_by(id=store_data['store_id']).first()
                if store:
                    store.store_name = store_data.get('store_name', store.store_name)
                    store.store_address = store_data.get('store_address', store.store_address)
                    store.updated_at = datetime.now(UTC)
                else:
                    new_store = PathaoStore(
                        id=store_data['store_id'],
                        store_name=store_data.get('store_name', ''),
                        store_address=store_data.get('store_address', ''),
                        updated_at=datetime.now(UTC)
                    )
                    db.session.add(new_store)
            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Error updating stores cache: {str(e)}")
            db.session.rollback()


    @classmethod
    def create_order(cls, order, store_id=None):
        """Create order in Pathao system with specified store"""
        try:
            token = cls.get_access_token()
            if not token:
                return {'code': 400, 'message': 'Failed to get access token'}
            
            customer = order.customer
            
            # Use provided store_id or fallback to default
            if store_id is None:
                current_app.logger.error(f"Error creating Pathao order: No store found")
                return {'code': 500, 'message': f'Failed to create order: No store found'}
            
            config = cls.get_config()
            order_data = {
                "store_id": int(store_id),
                "merchant_order_id": str(order.id),
                "recipient_name": customer.name,
                "recipient_phone": customer.phone,
                "recipient_address": customer.address,
                "recipient_city": order.city_id,
                "recipient_zone": order.zone_id,
                "delivery_type": 48,
                "item_type": 2,  # 2 for parcel
                "item_quantity": order.item_count,
                "item_weight": float(0.5),
                "item_description": "Mixed order",
                "amount_to_collect": int(order.total_amount),
            }
            url = f"{config['BASE_URL']}/aladdin/api/v1/orders"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=order_data, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            current_app.logger.error(f"Error creating Pathao order: {str(e)}")
            return {'code': 500, 'message': f'Failed to create order: {str(e)}'}
