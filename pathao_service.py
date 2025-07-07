import requests
import json
from datetime import datetime, timedelta
from models import db, PathaoCity, PathaoZone, PathaoArea, PathaoToken
from flask import current_app

class PathaoService:
    BASE_URL = "https://courier-api-sandbox.pathao.com"
    CLIENT_ID = "7N1aMJQbWm"
    CLIENT_SECRET = "wRcaibZkUdSNz2EI9ZyuXLlNrnAv0TdPUPXMnD39"
    USERNAME = "test@pathao.com"
    PASSWORD = "lovePathao"
    GRANT_TYPE = "password"
    
    CACHE_DURATION_HOURS = 24  # Cache location data for 24 hours
    
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
            url = f"{cls.BASE_URL}/aladdin/api/v1/issue-token"
            payload = {
                "client_id": cls.CLIENT_ID,
                "client_secret": cls.CLIENT_SECRET,
                "grant_type": cls.GRANT_TYPE,
                "username": cls.USERNAME,
                "password": cls.PASSWORD
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate expiry time (subtract 1 hour for safety)
            expires_in = data.get('expires_in', 432000)  # Default 5 days
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 3600)
            
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
            url = f"{cls.BASE_URL}/aladdin/api/v1/issue-token"
            payload = {
                "client_id": cls.CLIENT_ID,
                "client_secret": cls.CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate expiry time
            expires_in = data.get('expires_in', 432000)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 3600)
            
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
                cache_cutoff = datetime.utcnow() - timedelta(hours=cls.CACHE_DURATION_HOURS)
                cached_cities = PathaoCity.query.filter(
                    PathaoCity.last_updated > cache_cutoff
                ).all()
                
                if cached_cities:
                    return cached_cities
            
            # Fetch from API
            access_token = cls.get_access_token()
            if not access_token:
                return []
            
            url = f"{cls.BASE_URL}/aladdin/api/v1/city-list"
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
    def get_zones(cls, city_id, force_refresh=False):
        """Get zones for a city with caching"""
        try:
            # Check cache first
            if not force_refresh:
                cache_cutoff = datetime.utcnow() - timedelta(hours=cls.CACHE_DURATION_HOURS)
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
            
            url = f"{cls.BASE_URL}/aladdin/api/v1/cities/{city_id}/zone-list"
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
    def get_areas(cls, zone_id, force_refresh=False):
        """Get areas for a zone with caching"""
        try:
            # Check cache first
            if not force_refresh:
                cache_cutoff = datetime.utcnow() - timedelta(hours=cls.CACHE_DURATION_HOURS)
                cached_areas = PathaoArea.query.filter(
                    PathaoArea.zone_id == zone_id,
                    PathaoArea.last_updated > cache_cutoff
                ).all()
                
                if cached_areas:
                    return cached_areas
            
            # Fetch from API
            access_token = cls.get_access_token()
            if not access_token:
                return []
            
            url = f"{cls.BASE_URL}/aladdin/api/v1/zones/{zone_id}/area-list"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            areas_data = data.get('data', {}).get('data', [])
            
            # Update cache
            cls._update_areas_cache(zone_id, areas_data)
            
            # Return updated cache
            return PathaoArea.query.filter_by(zone_id=zone_id).all()
            
        except Exception as e:
            current_app.logger.error(f"Error fetching areas for zone {zone_id}: {str(e)}")
            # Return cached data even if stale
            return PathaoArea.query.filter_by(zone_id=zone_id).all()
    
    @classmethod
    def _update_cities_cache(cls, cities_data):
        """Update cities cache in database"""
        try:
            for city_data in cities_data:
                city = PathaoCity.query.filter_by(city_id=city_data['city_id']).first()
                if city:
                    city.city_name = city_data['city_name']
                    city.last_updated = datetime.utcnow()
                else:
                    city = PathaoCity(
                        city_id=city_data['city_id'],
                        city_name=city_data['city_name'],
                        last_updated=datetime.utcnow()
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
                    zone.last_updated = datetime.utcnow()
                else:
                    zone = PathaoZone(
                        zone_id=zone_data['zone_id'],
                        zone_name=zone_data['zone_name'],
                        city_id=city_id,
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(zone)
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating zones cache: {str(e)}")
            db.session.rollback()
    
    @classmethod
    def _update_areas_cache(cls, zone_id, areas_data):
        """Update areas cache in database"""
        try:
            for area_data in areas_data:
                area = PathaoArea.query.filter_by(area_id=area_data['area_id']).first()
                if area:
                    area.area_name = area_data['area_name']
                    area.zone_id = zone_id
                    area.home_delivery_available = area_data.get('home_delivery_available', True)
                    area.pickup_available = area_data.get('pickup_available', True)
                    area.last_updated = datetime.utcnow()
                else:
                    area = PathaoArea(
                        area_id=area_data['area_id'],
                        area_name=area_data['area_name'],
                        zone_id=zone_id,
                        home_delivery_available=area_data.get('home_delivery_available', True),
                        pickup_available=area_data.get('pickup_available', True),
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(area)
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating areas cache: {str(e)}")
            db.session.rollback()
    
    @classmethod
    def get_location_names(cls, city_id=None, zone_id=None, area_id=None):
        """Get location names for given IDs"""
        result = {}
        
        if city_id:
            city = PathaoCity.query.filter_by(city_id=city_id).first()
            result['city_name'] = city.city_name if city else None
        
        if zone_id:
            zone = PathaoZone.query.filter_by(zone_id=zone_id).first()
            result['zone_name'] = zone.zone_name if zone else None
        
        if area_id:
            area = PathaoArea.query.filter_by(area_id=area_id).first()
            result['area_name'] = area.area_name if area else None
        
        return result
