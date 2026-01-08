"""
Hospital Scraper Service
Ethical web scraping for hospital details (OPD timings, departments, etc.).
"""
from typing import Optional, Dict, List
import time
import logging
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HospitalScraperService:
    """Service for scraping hospital websites for additional details"""
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize scraper service
        
        Args:
            mock_mode: If True, return mock data
        """
        self.mock_mode = mock_mode
        self.cache: Dict[str, tuple] = {}  # URL -> (data, timestamp)
        self.cache_ttl_hours = 24
        
        if mock_mode:
            logger.info("⚠️  Hospital Scraper in MOCK mode")
        else:
            logger.info("✅ Hospital Scraper initialized")
    
    def scrape_hospital_details(self, website_url: str, place_id: str) -> Dict:
        """
        Scrape hospital website for additional details
        
        Ethical guidelines:
        - Check robots.txt
        - 2-second delay between requests
        - Respect noindex directives
        - User-Agent header
        - Cache results (24h TTL)
        
        Args:
            website_url: Hospital website URL
            place_id: Google Maps place_id
            
        Returns:
            Dict with scraped data
        """
        if self.mock_mode:
            return self._get_mock_details(place_id)
        
        # Check cache first
        if website_url in self.cache:
            cached_data, timestamp = self.cache[website_url]
            if datetime.now() - timestamp < timedelta(hours=self.cache_ttl_hours):
                logger.info(f"📦 Using cached data for {website_url}")
                return cached_data
        
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.robotparser import RobotFileParser
            
            # 1. Check robots.txt
            if not self._check_robots_txt(website_url):
                logger.warning(f"⚠️  robots.txt disallows scraping: {website_url}")
                return self._get_mock_details(place_id)
            
            # 2. Add delay (be polite)
            time.sleep(2)
            
            # 3. Fetch page with proper User-Agent
            headers = {
                'User-Agent': 'AuraHealth/1.0 (Healthcare App; Educational Purpose)'
            }
            
            response = requests.get(website_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 4. Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for noindex
            meta_robots = soup.find('meta', attrs={'name': 'robots'})
            if meta_robots and 'noindex' in meta_robots.get('content', '').lower():
                logger.warning(f"⚠️  Page has noindex directive: {website_url}")
                return self._get_mock_details(place_id)
            
            # 5. Extract structured data
            scraped_data = {
                "opd_timings": self._extract_timings(soup),
                "departments": self._extract_departments(soup),
                "emergency_number": self._extract_emergency_contact(soup),
                "bed_availability": None,  # Often requires dynamic JS
                "last_scraped": datetime.now().isoformat()
            }
            
            # 6. Cache results
            self.cache[website_url] = (scraped_data, datetime.now())
            
            logger.info(f"✅ Scraped hospital details from {website_url}")
            return scraped_data
            
        except Exception as e:
            logger.error(f"❌ Scraping failed for {website_url}: {e}")
            return self._get_mock_details(place_id)
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check if robots.txt allows crawling"""
        try:
            from urllib.robotparser import RobotFileParser
            
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = "AuraHealth/1.0"
            can_fetch = rp.can_fetch(user_agent, url)
            
            return can_fetch
            
        except Exception as e:
            logger.warning(f"⚠️  Could not check robots.txt: {e}")
            return True  # Allow if can't read robots.txt
    
    def _extract_timings(self, soup) -> Optional[str]:
        """Extract OPD/visiting hours from HTML"""
        # Look for common patterns
        patterns = [
            r'OPD.*?(\d{1,2}:\d{2}\s*(?:AM|PM)?.*?\d{1,2}:\d{2}\s*(?:AM|PM)?)',
            r'Visiting Hours?:?\s*(\d{1,2}:\d{2}.*?\d{1,2}:\d{2})',
            r'Timings?:?\s*(\d{1,2}\s*(?:AM|PM).*?\d{1,2}\s*(?:AM|PM))'
        ]
        
        text = soup.get_text()
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_departments(self, soup) -> List[str]:
        """Extract list of departments/specialties"""
        departments = []
        
        # Common department keywords
        keywords = [
            'Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics',
            'Gynecology', 'Oncology', 'Emergency', 'ICU',
            'Radiology', 'Pathology', 'Surgery', 'Medicine'
        ]
        
        text = soup.get_text()
        
        for keyword in keywords:
            if keyword.lower() in text.lower():
                departments.append(keyword)
        
        return departments[:10]  # Limit to 10
    
    def _extract_emergency_contact(self, soup) -> Optional[str]:
        """Extract emergency contact number"""
        # Look for emergency numbers
        patterns = [
            r'Emergency:?\s*(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'24x7:?\s*(\+?\d{10,})',
            r'Ambulance:?\s*(\+?\d{10,})'
        ]
        
        text = soup.get_text()
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _get_mock_details(self, place_id: str) -> Dict:
        """Generate mock scraped data"""
        mock_data = {
            "opd_timings": "9:00 AM - 8:00 PM (Mon-Sat), 9:00 AM - 1:00 PM (Sun)",
            "departments": ["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Emergency"],
            "emergency_number": "+91 9876543210",
            "bed_availability": "Limited beds available",
            "last_scraped": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Generated mock hospital details for {place_id}")
        return mock_data


# Global service instance
scraper_service: Optional[HospitalScraperService] = None


def init_scraper_service(mock_mode: bool = True) -> HospitalScraperService:
    """Initialize the global scraper service"""
    global scraper_service
    scraper_service = HospitalScraperService(mock_mode)
    return scraper_service


def get_scraper_service() -> HospitalScraperService:
    """Get the global scraper service instance"""
    if scraper_service is None:
        raise RuntimeError("Scraper service not initialized")
    return scraper_service
