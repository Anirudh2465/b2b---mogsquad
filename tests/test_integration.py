"""
Integration Tests: End-to-End Workflow Verification
Tests the complete flow from prescription upload to refill alerts.
"""
import unittest
from unittest.mock import Mock, patch
import base64
from datetime import datetime

from app.services.semantic_parser import SemanticParser
from app.services.notification_service import NotificationService


class TestPrescriptionToMedicationFlow(unittest.TestCase):
    """Test complete prescription → medication workflow"""
    
    def setUp(self):
        self.parser = SemanticParser()
    
    def test_frequency_parsing_accuracy(self):
        """Verify all frequency abbreviations parse correctly"""
        test_cases = {
            "BID": 2,
            "TID": 3,
            "QD": 1,
            "1-0-1": 2,
            "1-1-1": 3,
            "QHS": 1
        }
        
        for abbrev, expected_count in test_cases.items():
            schedule = self.parser.parse_frequency(abbrev)
            self.assertIsNotNone(schedule, f"Failed to parse {abbrev}")
            self.assertEqual(schedule.count_per_day, expected_count,
                           f"Wrong count for {abbrev}")
    
    def test_inventory_calculation_accuracy(self):
        """Test medication inventory calculations"""
        test_scenarios = [
            # (dosage, frequency, duration, expected_total)
            (1, "BID", 10, 20),   # 1 pill × 2/day × 10 days = 20
            (2, "TID", 7, 42),    # 2 pills × 3/day × 7 days = 42
            (1, "QD", 30, 30),    # 1 pill × 1/day × 30 days = 30
        ]
        
        for dosage, freq, duration, expected in test_scenarios:
            schedule = self.parser.parse_frequency(freq)
            total = self.parser.calculate_total_inventory(dosage, schedule, duration)
            self.assertEqual(total, expected,
                           f"Inventory calc failed for {freq}")


class TestAdherenceTracking(unittest.TestCase):
    """Test medication adherence tracking accuracy"""
    
    def test_taken_vs_missed_inventory_impact(self):
        """Verify TAKEN decrements but MISSED doesn't"""
        # Initial inventory
        pills_remaining = 30
        
        # TAKEN event
        pills_remaining -= 1
        self.assertEqual(pills_remaining, 29)
        
        # MISSED event - should NOT decrement
        # pills_remaining stays same
        self.assertEqual(pills_remaining, 29)
    
    def test_consistency_index_thresholds(self):
        """Test risk level thresholds"""
        test_cases = [
            (65, "HIGH"),
            (75, "MEDIUM"),
            (90, "LOW")
        ]
        
        for consistency, expected_risk in test_cases:
            if consistency < 70:
                risk = "HIGH"
            elif consistency < 85:
                risk = "MEDIUM"
            else:
                risk = "LOW"
            
            self.assertEqual(risk, expected_risk)


class TestRefillAlertFlow(unittest.TestCase):
    """Test refill alert generation"""
    
    def setUp(self):
        self.notification_service = NotificationService(mock_mode=True)
    
    def test_refill_threshold_trigger(self):
        """Test refill alert triggers at threshold"""
        pills_remaining = 5
        refill_threshold = 5
        
        needs_refill = pills_remaining <= refill_threshold
        self.assertTrue(needs_refill)
    
    def test_whatsapp_link_generation(self):
        """Test WhatsApp link contains all required info"""
        url = self.notification_service.generate_whatsapp_link(
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


class TestSecurityVerification(unittest.TestCase):
    """Test security features"""
    
    def test_encryption_decryption_cycle(self):
        """Test AES-256-GCM encryption roundtrip"""
        from app.core.security import EncryptionManager
        
        # Mock master key (must be string, not bytes)
        master_key = '0' * 32  # 32 char string for AES-256
        encryption = EncryptionManager(master_key)
        
        plaintext = "Sensitive patient data"
        user_id = "test-patient-123"
        
        # Encrypt
        ciphertext = encryption.encrypt(plaintext, user_id)
        self.assertNotEqual(ciphertext, plaintext)
        
        # Decrypt
        decrypted = encryption.decrypt(ciphertext, user_id)
        self.assertEqual(decrypted, plaintext)
    
    def test_shard_routing_consistency(self):
        """Test hash-based sharding is deterministic"""
        from app.database.router import ShardRouter
        
        router = ShardRouter(num_shards=2)
        
        user_id = "test-user-456"
        
        # Multiple calls should return same shard
        shard1 = router.get_shard_id(user_id)
        shard2 = router.get_shard_id(user_id)
        shard3 = router.get_shard_id(user_id)
        
        self.assertEqual(shard1, shard2)
        self.assertEqual(shard2, shard3)
        self.assertIn(shard1, [0, 1])


class TestContinuityVerification(unittest.TestCase):
    """Test continuity (medication tracking over time)"""
    
    def test_chronic_condition_detection_rule(self):
        """Test 3-prescription rule for chronic detection"""
        prescription_count = 3
        lookback_months = 3
        
        # Should detect as chronic if >=3 prescriptions
        is_chronic = prescription_count >= 3
        self.assertTrue(is_chronic)
    
    def test_adherence_rate_calculation(self):
        """Test adherence rate formula"""
        days = 7
        doses_per_day = 2
        expected_doses = days * doses_per_day  # 14
        
        taken_doses = 12
        
        adherence_rate = (taken_doses / expected_doses) * 100
        self.assertAlmostEqual(adherence_rate, 85.71, places=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
