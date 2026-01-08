"""
Notification Service
Handles WhatsApp deep links and SMS via Twilio for pharmacy communication.
"""
import urllib.parse
from typing import Optional
import logging

from app.core.config import get_config

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending refill notifications"""
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize notification service
        
        Args:
            mock_mode: If True, don't actually send messages
        """
        self.mock_mode = mock_mode
        
        if not mock_mode:
            config = get_config()
            twilio_creds = config.get_api_key('twilio')
            self.twilio_account_sid = twilio_creds.get('account_sid')
            self.twilio_auth_token = twilio_creds.get('auth_token')
            self.twilio_phone = twilio_creds.get('phone_number', '+1234567890')
        else:
            logger.info("⚠️  Notification service in MOCK mode")
    
    def generate_whatsapp_link(self,
                              pharmacy_phone: str,
                              drug_name: str,
                              strength: str,
                              pills_remaining: int,
                              pills_needed: int,
                              pharmacy_name: Optional[str] = None) -> str:
        """
        Generate WhatsApp deep link for refill request
        
        Args:
            pharmacy_phone: Pharmacy WhatsApp number (e.g., "919876543210")
            drug_name: Medication name
            strength: Dosage strength
            pills_remaining: Current pill count
            pills_needed: Pills to order
            pharmacy_name: Pharmacy name (optional)
            
        Returns:
            WhatsApp deep link URL
        """
        # Clean phone number (remove spaces, dashes)
        clean_phone = pharmacy_phone.replace(' ', '').replace('-', '').replace('+', '')
        
        # Construct message
        greeting = f"Hello {pharmacy_name}," if pharmacy_name else "Hello,"
        message = (
            f"{greeting}\n\n"
            f"I would like to order a refill for:\n"
            f"💊 {drug_name} ({strength})\n\n"
            f"Current stock: {pills_remaining} pills\n"
            f"Required: {pills_needed} pills\n\n"
            f"Please confirm availability and total cost.\n\n"
            f"Thank you!"
        )
        
        # URL encode message
        encoded_msg = urllib.parse.quote(message)
        
        # Generate WhatsApp link
        whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"
        
        logger.info(f"📱 Generated WhatsApp link for {pharmacy_name or 'pharmacy'}")
        return whatsapp_url
    
    def send_sms_refill(self,
                       to_phone: str,
                       drug_name: str,
                       strength: str,
                       pills_needed: int,
                       pharmacy_name: Optional[str] = None) -> bool:
        """
        Send SMS refill request via Twilio
        
        Args:
            to_phone: Pharmacy phone number
            drug_name: Medication name
            strength: Dosage strength
            pills_needed: Pills to order
            pharmacy_name: Pharmacy name (optional)
            
        Returns:
            True if sent successfully
        """
        if self.mock_mode:
            logger.info(f"📲 [MOCK] Would send SMS to {to_phone}")
            return True
        
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            message_body = (
                f"Refill Request:\n"
                f"{drug_name} ({strength})\n"
                f"Quantity: {pills_needed} pills\n"
                f"Please confirm availability."
            )
            
            message = client.messages.create(
                to=to_phone,
                from_=self.twilio_phone,
                body=message_body
            )
            
            logger.info(f"✅ SMS sent to {to_phone}. SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send SMS: {e}")
            return False
    
    def generate_refill_notification(self,
                                    medication_data: dict) -> dict:
        """
        Generate refill notification with both WhatsApp and SMS options
        
        Args:
            medication_data: Dict with medication and pharmacy info
            
        Returns:
            Dict with WhatsApp URL and SMS status
        """
        pharmacy_phone = medication_data.get('pharmacy_phone')
        
        if not pharmacy_phone:
            logger.warning("⚠️  No pharmacy phone number available")
            return {"success": False, "error": "No pharmacy contact"}
        
        # Calculate pills needed (assume 30-day refill)
        pills_remaining = medication_data.get('pills_remaining', 0)
        pills_needed = max(30 - pills_remaining, 10)  # At least 10 pills
        
        whatsapp_url = self.generate_whatsapp_link(
            pharmacy_phone=pharmacy_phone,
            drug_name=medication_data['drug_name'],
            strength=medication_data['strength'],
            pills_remaining=pills_remaining,
            pills_needed=pills_needed,
            pharmacy_name=medication_data.get('pharmacy_name')
        )
        
        return {
            "success": True,
            "whatsapp_url": whatsapp_url,
            "pharmacy_phone": pharmacy_phone,
            "pills_needed": pills_needed,
            "message": "Refill notification generated"
        }


# Global notification service
notification_service: Optional[NotificationService] = None


def init_notification_service(mock_mode: bool = True) -> NotificationService:
    """Initialize the global notification service"""
    global notification_service
    notification_service = NotificationService(mock_mode)
    return notification_service


def get_notification_service() -> NotificationService:
    """Get the global notification service instance"""
    if notification_service is None:
        raise RuntimeError("Notification service not initialized")
    return notification_service
