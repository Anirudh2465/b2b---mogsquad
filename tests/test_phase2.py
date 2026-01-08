"""
Unit Tests for Phase 2: OCR, Semantic Parser, and Inventory
"""
import unittest
from datetime import datetime

from app.services.semantic_parser import SemanticParser
from app.services.notification_service import NotificationService


class TestSemanticParser(unittest.TestCase):
    """Test medical abbreviation parser"""
    
    def setUp(self):
        self.parser = SemanticParser()
    
    def test_parse_bid(self):
        """Test BID (twice daily) parsing"""
        schedule = self.parser.parse_frequency("BID")
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.count_per_day, 2)
        self.assertEqual(len(schedule.times), 2)
    
    def test_parse_tid(self):
        """Test TID (three times daily)"""
        schedule = self.parser.parse_frequency("TID")
        self.assertEqual(schedule.count_per_day, 3)
        self.assertEqual(len(schedule.times), 3)
    
    def test_parse_indian_notation(self):
        """Test Indian notation 1-0-1"""
        schedule = self.parser.parse_frequency("1-0-1")
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.count_per_day, 2)
        self.assertEqual(schedule.times, ["09:00", "21:00"])
    
    def test_parse_case_insensitive(self):
        """Test case-insensitive parsing"""
        schedule1 = self.parser.parse_frequency("bid")
        schedule2 = self.parser.parse_frequency("BID")
        schedule3 = self.parser.parse_frequency("Bid")
        
        self.assertEqual(schedule1.count_per_day, schedule2.count_per_day)
        self.assertEqual(schedule2.count_per_day, schedule3.count_per_day)
    
    def test_calculate_total_inventory(self):
        """Test inventory calculation"""
        schedule = self.parser.parse_frequency("BID")
        total = self.parser.calculate_total_inventory(
            dosage_per_intake=1,
            frequency=schedule,
            duration_days=10
        )
        self.assertEqual(total, 20)  # 1 × 2 × 10
    
    def test_calculate_inventory_tid(self):
        """Test three times daily inventory"""
        schedule = self.parser.parse_frequency("TID")
        total = self.parser.calculate_total_inventory(
            dosage_per_intake=2,  # 2 pills per dose
            frequency=schedule,
            duration_days=7
        )
        self.assertEqual(total, 42)  # 2 × 3 × 7
    
    def test_parse_unknown_frequency(self):
        """Test handling unknown frequency"""
        schedule = self.parser.parse_frequency("INVALID_FREQ")
        self.assertIsNone(schedule)
    
    def test_extract_dosage(self):
        """Test dosage extraction from text"""
        self.assertEqual(self.parser.extract_dosage_from_text("1 tablet"), 1)
        self.assertEqual(self.parser.extract_dosage_from_text("2 pills"), 2)
        self.assertEqual(self.parser.extract_dosage_from_text("500mg"), 500)


class TestNotificationService(unittest.TestCase):
    """Test notification service"""
    
    def setUp(self):
        self.service = NotificationService(mock_mode=True)
    
    def test_generate_whatsapp_link(self):
        """Test WhatsApp deep link generation"""
        url = self.service.generate_whatsapp_link(
            pharmacy_phone="919876543210",
            drug_name="Paracetamol",
            strength="500mg",
            pills_remaining=3,
            pills_needed=27,
            pharmacy_name="ABC Pharmacy"
        )
        
        self.assertIn("wa.me", url)
        self.assertIn("919876543210", url)
        self.assertIn("Paracetamol", url)
        self.assertIn("500mg", url)
    
    def test_whatsapp_link_phone_cleaning(self):
        """Test phone number cleaning"""
        url1 = self.service.generate_whatsapp_link(
            pharmacy_phone="+91 98765 43210",
            drug_name="Test",
            strength="100mg",
            pills_remaining=0,
            pills_needed=10
        )
        
        url2 = self.service.generate_whatsapp_link(
            pharmacy_phone="919876543210",
            drug_name="Test",
            strength="100mg",
            pills_remaining=0,
            pills_needed=10
        )
        
        # Both should produce same phone number
        self.assertIn("919876543210", url1)
        self.assertIn("919876543210", url2)
    
    def test_generate_refill_notification(self):
        """Test complete refill notification"""
        medication_data = {
            "drug_name": "Aspirin",
            "strength": "75mg",
            "pills_remaining": 2,
            "pharmacy_name": "XYZ Pharmacy",
            "pharmacy_phone": "9123456789"
        }
        
        result = self.service.generate_refill_notification(medication_data)
        
        self.assertTrue(result["success"])
        self.assertIn("whatsapp_url", result)
        self.assertGreater(result["pills_needed"], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
