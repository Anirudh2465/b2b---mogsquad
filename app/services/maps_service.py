"""
Google Maps Service
Geo-spatial discovery of nearby hospitals with smart ranking.
"""
from typing import List, Optional, Tuple
import logging
import math

from app.models.hospital import HospitalData

logger = logging.getLogger(__name__)


class MapsService:
    """Service for Google Maps Places API integration"""
    
    def __init__(self, mock_mode: bool = True, api_key: Optional[str] = None):
        """
        Initialize Maps service
        
        Args:
            mock_mode: If True, return mock hospital data
            api_key: Google Maps API key
        """
        self.mock_mode = mock_mode
        self.api_key = api_key
        
        if not mock_mode and api_key:
            try:
                import googlemaps
                self.client = googlemaps.Client(key=api_key)
                logger.info("✅ Google Maps client initialized")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Maps: {e}. Using mock mode.")
                self.mock_mode = True
        else:
            logger.info("⚠️  Maps service in MOCK mode")
    
    def search_nearby_hospitals(self,
                               latitude: float,
                               longitude: float,
                               radius_meters: int = 10000,
                               max_results: int = 20) -> List[HospitalData]:
        """
        Search for hospitals within radius
        
        Args:
            latitude: User's latitude
            longitude: User's longitude
            radius_meters: Search radius (default: 10km)
            max_results: Maximum results to return
            
        Returns:
            List of HospitalData objects
        """
        if self.mock_mode:
            return self._get_mock_hospitals(latitude, longitude)
        
        try:
            # Use Places API (New) - Nearby Search
            import requests
            
            url = "https://places.googleapis.com/v1/places:searchNearby"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount"
            }
            
            payload = {
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": latitude,
                            "longitude": longitude
                        },
                        "radius": radius_meters
                    }
                },
                "includedTypes": ["hospital", "medical_center"],
                "maxResultCount": max_results
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            hospitals = []
            
            for place in data.get('places', []):
                hospital = HospitalData.from_maps_result(place, (latitude, longitude))
                hospital.distance_meters = self._calculate_distance(
                    latitude, longitude,
                    hospital.latitude, hospital.longitude
                )
                hospitals.append(hospital)
            
            logger.info(f"✅ Found {len(hospitals)} hospitals via Maps API")
            return hospitals
            
        except Exception as e:
            logger.error(f"❌ Maps API error: {e}")
            return self._get_mock_hospitals(latitude, longitude)
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def rank_hospitals(self,
                      hospitals: List[HospitalData],
                      visited_place_ids: List[str]) -> List[HospitalData]:
        """
        Rank hospitals with smart scoring
        
        Ranking formula:
        score = (visited_before ? 100 : 0) + (rating * 10) - (distance / 1000)
        
        Args:
            hospitals: List of hospitals
            visited_place_ids: List of place_ids user has visited
            
        Returns:
            Sorted list of hospitals
        """
        for hospital in hospitals:
            hospital.visited_before = hospital.place_id in visited_place_ids
            
            visited_bonus = 100 if hospital.visited_before else 0
            rating_score = (hospital.rating or 0) * 10
            distance_penalty = (hospital.distance_meters or 0) / 1000
            
            hospital.rank_score = visited_bonus + rating_score - distance_penalty
        
        # Sort by rank score descending
        ranked = sorted(hospitals, key=lambda h: h.rank_score, reverse=True)
        
        logger.info(f"📊 Ranked {len(ranked)} hospitals")
        return ranked
    
    def _get_mock_hospitals(self, latitude: float, longitude: float) -> List[HospitalData]:
        """Generate mock hospital data for testing"""
        mock_hospitals = [
            HospitalData(
                place_id="mock_hospital_1",
                name="City General Hospital",
                formatted_address="123 Main Street, City Center",
                latitude=latitude + 0.01,
                longitude=longitude + 0.01,
                distance_meters=1500,
                phone_number="+919876543210",
                website="https://cityhospital.example.com",
                rating=4.5,
                user_ratings_total=1250,
                opd_timings=None,
                departments=[],
                emergency_number=None,
                bed_availability=None,
                visited_before=False,
                rank_score=0.0,
                last_scraped=None
            ),
            HospitalData(
                place_id="mock_hospital_2",
                name="St. Mary's Medical Center",
                formatted_address="456 Oak Avenue, Westside",
                latitude=latitude + 0.02,
                longitude=longitude - 0.01,
                distance_meters=3200,
                phone_number="+919123456789",
                website="https://stmarys.example.com",
                rating=4.2,
                user_ratings_total=890,
                opd_timings=None,
                departments=[],
                emergency_number=None,
                bed_availability=None,
                visited_before=False,
                rank_score=0.0,
                last_scraped=None
            ),
            HospitalData(
                place_id="mock_hospital_3",
                name="Apollo Multispecialty",
                formatted_address="789 Park Road, North Zone",
                latitude=latitude - 0.015,
                longitude=longitude + 0.02,
                distance_meters=2800,
                phone_number="+919988776655",
                website="https://apollo.example.com",
                rating=4.7,
                user_ratings_total=2100,
                opd_timings=None,
                departments=[],
                emergency_number=None,
                bed_availability=None,
                visited_before=False,
                rank_score=0.0,
                last_scraped=None
            )
        ]
        
        logger.info(f"✅ Generated {len(mock_hospitals)} mock hospitals")
        return mock_hospitals


# Global service instance
maps_service: Optional[MapsService] = None


def init_maps_service(mock_mode: bool = True, api_key: Optional[str] = None) -> MapsService:
    """Initialize the global Maps service"""
    global maps_service
    maps_service = MapsService(mock_mode, api_key)
    return maps_service


def get_maps_service() -> MapsService:
    """Get the global Maps service instance"""
    if maps_service is None:
        raise RuntimeError("Maps service not initialized")
    return maps_service
