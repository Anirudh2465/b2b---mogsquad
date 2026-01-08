"""
Voice Service
Twilio Programmable Voice integration for click-to-call functionality.
"""
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class VoiceService:
    """Service for Twilio Voice API integration"""
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize Voice service
        
        Args:
            mock_mode: If True, simulate calls without using Twilio
        """
        self.mock_mode = mock_mode
        
        if not mock_mode:
            try:
                from app.core.config import get_config
                config = get_config()
                
                twilio_creds = config.get_api_key('twilio')
                self.account_sid = twilio_creds.get('account_sid')
                self.auth_token = twilio_creds.get('auth_token')
                self.from_number = twilio_creds.get('phone_number')
                
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                
                logger.info("✅ Twilio Voice client initialized")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Twilio Voice: {e}. Using mock mode.")
                self.mock_mode = True
        else:
            logger.info("⚠️  Voice service in MOCK mode")
    
    def initiate_call(self,
                     patient_phone: str,
                     hospital_phone: str,
                     hospital_name: str) -> Dict:
        """
        Initiate a bridged call between patient and hospital
        
        Flow:
        1. Call patient's number
        2. When answered, connect to hospital number
        3. Log call details
        
        Args:
            patient_phone: Patient's phone number
            hospital_phone: Hospital's phone number
            hospital_name: Hospital name (for logging)
            
        Returns:
            Dict with call status and SID
        """
        if self.mock_mode:
            logger.info(f"📞 [MOCK] Would call {hospital_name} at {hospital_phone} for patient {patient_phone}")
            return {
                "success": True,
                "call_sid": "mock_call_sid_12345",
                "status": "initiated",
                "message": f"Mock call to {hospital_name}",
                "mock": True
            }
        
        try:
            # Generate TwiML to bridge the call
            twiml = f"""
            <Response>
                <Say>Connecting you to {hospital_name}. Please wait.</Say>
                <Dial callerId="{self.from_number}">
                    <Number>{hospital_phone}</Number>
                </Dial>
            </Response>
            """
            
            # Initiate call to patient
            call = self.client.calls.create(
                to=patient_phone,
                from_=self.from_number,
                twiml=twiml
            )
            
            logger.info(f"✅ Call initiated: {call.sid}")
            
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "message": f"Call to {hospital_name} initiated",
                "mock": False
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initiate call: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initiate call"
            }
    
    def get_call_status(self, call_sid: str) -> Dict:
        """
        Get status of an ongoing/completed call
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Dict with call details
        """
        if self.mock_mode:
            return {
                "call_sid": call_sid,
                "status": "completed",
                "duration": 120,
                "mock": True
            }
        
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "start_time": call.start_time,
                "end_time": call.end_time
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch call status: {e}")
            return {"error": str(e)}
    
    def send_appointment_sms(self,
                            patient_phone: str,
                            hospital_name: str,
                            appointment_details: str) -> bool:
        """
        Send appointment confirmation via SMS
        
        Args:
            patient_phone: Patient's phone number
            hospital_name: Hospital name
            appointment_details: Appointment info
            
        Returns:
            True if sent successfully
        """
        if self.mock_mode:
            logger.info(f"📱 [MOCK] Would send appointment SMS to {patient_phone}")
            return True
        
        try:
            message = self.client.messages.create(
                to=patient_phone,
                from_=self.from_number,
                body=f"Appointment confirmed at {hospital_name}\n\n{appointment_details}\n\nSave this message for reference."
            )
            
            logger.info(f"✅ Appointment SMS sent: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send SMS: {e}")
            return False


# Global service instance
voice_service: Optional[VoiceService] = None


def init_voice_service(mock_mode: bool = True) -> VoiceService:
    """Initialize the global Voice service"""
    global voice_service
    voice_service = VoiceService(mock_mode)
    return voice_service


def get_voice_service() -> VoiceService:
    """Get the global Voice service instance"""
    if voice_service is None:
        raise RuntimeError("Voice service not initialized")
    return voice_service
