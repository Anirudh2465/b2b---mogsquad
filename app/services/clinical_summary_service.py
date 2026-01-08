"""
Clinical Summary Service
Generates professional medical summaries using Google Gemini API.
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging

from app.models.digital_twin import DigitalTwinState

logger = logging.getLogger(__name__)


class ClinicalSummaryService:
    """Service for generating LLM-based clinical summaries using Google Gemini"""
    
    def __init__(self, mock_mode: bool = True, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        """
        Initialize clinical summary service with Google Gemini
        
        Args:
            mock_mode: If True, return mock summaries
            api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-1.5-flash)
                       Options: gemini-1.5-pro, gemini-1.5-flash, gemini-pro
        """
        self.mock_mode = mock_mode
        self.api_key = api_key
        self.model_name = model_name
        
        if not mock_mode:
            # Check for provider configuration
            from app.core.config import get_config
            config = get_config().get_api_key('gemini')
            self.provider = config.get('provider', 'google')
            
            try:
                if self.provider == 'openrouter':
                    self.api_key = config.get('api_key')
                    self.model_name = config.get('model_name', 'deepseek/deepseek-r1')
                    logger.info(f"✅ OpenRouter initialized with model: {self.model_name}")
                else:
                    # Google Gemini
                    import google.generativeai as genai
                    genai.configure(api_key=api_key or config.get('api_key'))
                    self.client = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Google Gemini client initialized with model: {model_name}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize LLM provider {self.provider}: {e}. Using mock mode.")
                self.mock_mode = True
        else:
            logger.info("⚠️  Clinical Summary service in MOCK mode")
    
    def generate_summary(self,
                        digital_twin: DigitalTwinState,
                        medication_history: List[Dict],
                        max_words: int = 150) -> str:
        """
        Generate professional clinical summary
        
        Args:
            digital_twin: Patient's Digital Twin state
            medication_history: List of medication records
            max_words: Maximum summary length
            
        Returns:
            Professional clinical abstract
        """
        if self.mock_mode:
            return self._generate_mock_summary(digital_twin, medication_history)
        
        # Construct prompt
        prompt = self._build_prompt(digital_twin, medication_history, max_words)
        
        try:
            if hasattr(self, 'provider') and self.provider == 'openrouter':
                # OpenRouter (DeepSeek) implementation using requests
                import requests
                import json
                
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://aurahealth.ai", # Required by OpenRouter
                        "X-Title": "AuraHealth"
                    },
                    data=json.dumps({
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": "You are a specialized medical assistant generating clinical summaries."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 300
                    })
                )
                
                response.raise_for_status()
                result = response.json()
                summary = result['choices'][0]['message']['content'].strip()
                logger.info(f"✅ Generated clinical summary via OpenRouter ({self.model_name})")
                return summary
            
            else:
                # Gemini implementation
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.3,
                        'max_output_tokens': 300,
                        'top_p': 0.8,
                        'top_k': 40
                    }
                )
                summary = response.text.strip()
                logger.info(f"✅ Generated clinical summary via Gemini ({self.model_name})")
                return summary
            
        except Exception as e:
            logger.error(f"❌ LLM summary generation failed: {e}")
            return self._generate_mock_summary(digital_twin, medication_history)
    
    def _build_prompt(self,
                     digital_twin: DigitalTwinState,
                     medication_history: List[Dict],
                     max_words: int) -> str:
        """Build LLM prompt for clinical summary"""
        
        # Format chronic conditions
        conditions_text = ", ".join([
            f"{c.condition_name} (detected {c.first_detected.strftime('%b %Y')})"
            for c in digital_twin.chronic_conditions
        ]) if digital_twin.chronic_conditions else "None detected"
        
        # Format active medications
        meds_text = "\n".join([
            f"- {med['drug_name']} {med['strength']}, {med['frequency']}"
            for med in medication_history[:10]  # Last 10 medications
        ])
        
        prompt = f"""Generate a {max_words}-word professional clinical summary for a patient.

Patient Data:
- Chronic Conditions: {conditions_text}
- Adherence Rate: {digital_twin.consistency_index:.1f}%
- Risk Level: {digital_twin.risk_level}
- Active Medications: {digital_twin.active_medications_count}
- Total Prescriptions: {digital_twin.total_prescriptions}

Recent Medications:
{meds_text}

Generate a concise clinical abstract including:
1. Overview of chronic conditions and duration
2. Current medication regimen
3. Adherence status and risk assessment
4. Any notable patterns or concerns

Keep it professional, factual, and within {max_words} words."""
        
        return prompt
    
    def _generate_mock_summary(self,
                               digital_twin: DigitalTwinState,
                               medication_history: List[Dict]) -> str:
        """Generate mock clinical summary (for testing)"""
        
        # Build conditions list
        if digital_twin.chronic_conditions:
            conditions_str = ", ".join([c.condition_name for c in digital_twin.chronic_conditions])
        else:
            conditions_str = "no chronic conditions detected"
        
        # Get recent medications
        recent_meds = medication_history[:3] if medication_history else []
        meds_str = ", ".join([f"{m.get('drug_name', 'Unknown')} {m.get('strength', '')}" 
                              for m in recent_meds])
        
        # Calculate months since first prescription
        if digital_twin.chronic_conditions:
            first_date = min([c.first_detected for c in digital_twin.chronic_conditions])
            months = (datetime.now() - first_date).days // 30
            history_str = f"{months}-month history"
        else:
            history_str = "recent history"
        
        summary = (
            f"Patient has a {history_str} with {conditions_str}. "
            f"Currently managing {digital_twin.active_medications_count} active medications"
        )
        
        if recent_meds:
            summary += f" including {meds_str}"
        
        summary += (
            f". Adherence rate is {digital_twin.consistency_index:.1f}%, "
            f"indicating {digital_twin.risk_level.lower()} risk of treatment failure."
        )
        
        if digital_twin.last_acute_episode:
            summary += f" Last acute episode: {digital_twin.last_acute_episode} in {digital_twin.last_acute_date.strftime('%b %Y')}."
        
        summary += (
            f" Patient has completed {digital_twin.total_prescriptions} prescriptions to date. "
            "Continued monitoring recommended for optimal health outcomes."
        )
        
        logger.info("✅ Generated mock clinical summary")
        return summary


# Global service instance
clinical_summary_service: Optional[ClinicalSummaryService] = None


def init_clinical_summary_service(mock_mode: bool = True, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash") -> ClinicalSummaryService:
    """Initialize the global clinical summary service with Google Gemini"""
    global clinical_summary_service
    clinical_summary_service = ClinicalSummaryService(mock_mode, api_key, model_name)
    return clinical_summary_service


def get_clinical_summary_service() -> ClinicalSummaryService:
    """Get the global clinical summary service instance"""
    if clinical_summary_service is None:
        raise RuntimeError("Clinical summary service not initialized")
    return clinical_summary_service
