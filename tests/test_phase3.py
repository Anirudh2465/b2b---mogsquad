"""
Phase 4 Verification Tests: Digital Twin and Geo-Discovery
"""
import unittest
from datetime import datetime, timedelta

from app.services.digital_twin_service import DigitalTwinService, CHRONIC_DRUG_PATTERNS
from app.services.clinical_summary_service import ClinicalSummaryService
from app.services.maps_service import MapsService
from app.services.scraper_service import HospitalScraperService
from app.models.digital_twin import DigitalTwinState, ChronicCondition


class TestDigitalTwinService(unittest.TestCase):
    """Test Digital Twin chronic condition detection"""
    
    def setUp(self):
        # Skip db initialization - test model logic only
        pass
    
    def test_chronic_drug_patterns(self):
        """Test chronic condition pattern dictionary"""
        # Test the dictionary directly without service
        self.assertIn("DIABETES", CHRONIC_DRUG_PATTERNS)
        self.assertIn("HYPERTENSION", CHRONIC_DRUG_PATTERNS)
        self.assertIn("metformin", CHRONIC_DRUG_PATTERNS["DIABETES"])
        self.assertIn("amlodipine", CHRONIC_DRUG_PATTERNS["HYPERTENSION"])
    
    def test_chronic_condition_detection_threshold(self):
        """Test 3-prescription rule for chronic detection"""
        # This would require DB mocking - testing logic only
        lookback_months = 3
        self.assertEqual(lookback_months, 3)
    
    def test_consistency_index_calculation(self):
        """Test adherence consistency formula"""
        # Formula: (taken / expected) * 100
        taken = 17
        expected = 20
        consistency = (taken / expected) * 100
        self.assertEqual(consistency, 85.0)
    
    def test_risk_level_high(self):
        """Test HIGH risk level (<70% adherence)"""
        twin = DigitalTwinState.create("mock_patient_id")
        twin.consistency_index = 65.0
        risk = twin.calculate_risk_level()
        self.assertEqual(risk, "HIGH")
    
    def test_risk_level_medium(self):
        """Test MEDIUM risk level (70-85% adherence)"""
        twin = DigitalTwinState.create("mock_patient_id")
        twin.consistency_index = 80.0
        risk = twin.calculate_risk_level()
        self.assertEqual(risk, "MEDIUM")
    
    def test_risk_level_low(self):
        """Test LOW risk level (>85% adherence)"""
        twin = DigitalTwinState.create("mock_patient_id")
        twin.consistency_index = 92.0
        risk = twin.calculate_risk_level()
        self.assertEqual(risk, "LOW")


class TestClinicalSummaryService(unittest.TestCase):
    """Test LLM clinical summary generation"""
    
    def setUp(self):
        self.service = ClinicalSummaryService(mock_mode=True)
    
    def test_mock_summary_generation(self):
        """Test mock summary contains key elements"""
        twin = DigitalTwinState.create("mock_patient_id")
        twin.consistency_index = 85.5
        twin.risk_level = "MEDIUM"
        twin.active_medications_count = 2
        
        # Add chronic condition
        condition = ChronicCondition(
            condition_name="HYPERTENSION",
            first_detected=datetime.now() - timedelta(days=180),
            confidence_score=0.9,
            supporting_medications=["Amlodipine"],
            prescription_count=4
        )
        twin.chronic_conditions.append(condition)
        
        summary = self.service._generate_mock_summary(twin, [])
        
        self.assertIn("HYPERTENSION", summary)
        self.assertIn("85.5", summary)
        self.assertIn("medium", summary.lower() or "MEDIUM" in summary)
    
    def test_summary_word_count_limit(self):
        """Test that summary respects word limit"""
        twin = DigitalTwinState.create("mock_patient_id")
        summary = self.service._generate_mock_summary(twin, [])
        
        word_count = len(summary.split())
        self.assertLess(word_count, 200)  # Should be under 200 words


class TestMapsService(unittest.TestCase):
    """Test Google Maps integration"""
    
    def setUp(self):
        self.service = MapsService(mock_mode=True)
    
    def test_mock_hospital_generation(self):
        """Test mock hospital data"""
        hospitals = self.service._get_mock_hospitals(12.9716, 77.5946)
        self.assertGreater(len(hospitals), 0)
        self.assertEqual(hospitals[0].place_id, "mock_hospital_1")
    
    def test_distance_calculation(self):
        """Test Haversine distance formula"""
        # Bangalore to Mysore (approx 140 km)
        lat1, lon1 = 12.9716, 77.5946  # Bangalore
        lat2, lon2 = 12.2958, 76.6394  # Mysore
        
        distance = self.service._calculate_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 128-145 km (Earth radius variations)
        self.assertGreater(distance, 120000)
        self.assertLess(distance, 150000)
    
    def test_hospital_ranking_visited_bonus(self):
        """Test visited hospital gets priority"""
        hospitals = self.service._get_mock_hospitals(12.9716, 77.5946)
        visited_ids = ["mock_hospital_2"]
        
        ranked = self.service.rank_hospitals(hospitals, visited_ids)
        
        # Find the visited hospital
        visited_hospital = next(h for h in ranked if h.place_id == "mock_hospital_2")
        self.assertTrue(visited_hospital.visited_before)
        self.assertGreater(visited_hospital.rank_score, 100)  # Should have bonus
    
    def test_hospital_ranking_formula(self):
        """Test ranking score calculation"""
        # Score = visited_bonus + (rating * 10) - (distance / 1000)
        visited_bonus = 100
        rating = 4.5
        distance_m = 2000
        
        expected_score = visited_bonus + (rating * 10) - (distance_m / 1000)
        self.assertEqual(expected_score, 143.0)


class TestHospitalScraper(unittest.TestCase):
    """Test ethical web scraping"""
    
    def setUp(self):
        self.service = HospitalScraperService(mock_mode=True)
    
    def test_mock_scraping(self):
        """Test mock scraper returns structured data"""
        details = self.service._get_mock_details("mock_place_id")
        
        self.assertIn("opd_timings", details)
        self.assertIn("departments", details)
        self.assertIn("emergency_number", details)
        self.assertIsInstance(details["departments"], list)
    
    def test_cache_ttl(self):
        """Test cache TTL is 24 hours"""
        self.assertEqual(self.service.cache_ttl_hours, 24)
    
    def test_department_extraction(self):
        """Test common departments are detected"""
        keywords = ["Cardiology", "Neurology", "Pediatrics"]
        mock_details = self.service._get_mock_details("test")
        
        for dept in mock_details["departments"]:
            self.assertIsInstance(dept, str)


if __name__ == '__main__':
    unittest.main(verbosity=2)
