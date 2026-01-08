"""
Hospital Data Model
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class HospitalData:
    """Hospital information from Google Maps + scraping"""
    
    place_id: str  # Google Maps place_id
    name: str
    formatted_address: str
    
    # Location
    latitude: float
    longitude: float
    distance_meters: Optional[float]
    
    # Contact
    phone_number: Optional[str]
    website: Optional[str]
    
    # Rating
    rating: Optional[float]
    user_ratings_total: Optional[int]
    
    # Scraped details
    opd_timings: Optional[str]
    departments: List[str]
    emergency_number: Optional[str]
    bed_availability: Optional[str]
    
    # Ranking
    visited_before: bool
    rank_score: float
    
    # Metadata
    last_scraped: Optional[datetime]
    
    @classmethod
    def from_maps_result(cls, result: dict, user_location: tuple):
        """Create from Google Maps API result"""
        location = result.get('location', {})
        
        return cls(
            place_id=result.get('id', ''),
            name=result.get('displayName', {}).get('text', 'Unknown'),
            formatted_address=result.get('formattedAddress', ''),
            latitude=location.get('latitude', 0.0),
            longitude=location.get('longitude', 0.0),
            distance_meters=None,  # Calculate separately
            phone_number=result.get('nationalPhoneNumber'),
            website=result.get('websiteUri'),
            rating=result.get('rating'),
            user_ratings_total=result.get('userRatingCount'),
            opd_timings=None,
            departments=[],
            emergency_number=None,
            bed_availability=None,
            visited_before=False,
            rank_score=0.0,
            last_scraped=None
        )


@dataclass
class HospitalVisit:
    """Record of patient hospital visit"""
    
    visit_id: str
    patient_id: str
    place_id: str
    hospital_name: str
    visit_date: datetime
    purpose: Optional[str]
