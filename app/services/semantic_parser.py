"""
Semantic Parser for Medical Abbreviations
Translates doctor shorthand (sigs) into machine-readable logic.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrequencySchedule:
    """Parsed frequency schedule"""
    count_per_day: int
    times: List[str]  # 24-hour format times (e.g., ["09:00", "21:00"])
    abbreviation: str


# Medical frequency abbreviations mapping
FREQUENCY_MAP: Dict[str, FrequencySchedule] = {
    # Once daily
    "QD": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="QD"),
    "OD": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="OD"),
    "ONCE DAILY": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="QD"),
    "1X/DAY": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="QD"),
    
    # Twice daily
    "BID": FrequencySchedule(count_per_day=2, times=["09:00", "21:00"], abbreviation="BID"),
    "BD": FrequencySchedule(count_per_day=2, times=["09:00", "21:00"], abbreviation="BID"),
    "TWICE DAILY": FrequencySchedule(count_per_day=2, times=["09:00", "21:00"], abbreviation="BID"),
    "2X/DAY": FrequencySchedule(count_per_day=2, times=["09:00", "21:00"], abbreviation="BID"),
    
    # Three times daily
    "TID": FrequencySchedule(count_per_day=3, times=["09:00", "14:00", "21:00"], abbreviation="TID"),
    "TD": FrequencySchedule(count_per_day=3, times=["09:00", "14:00", "21:00"], abbreviation="TID"),
    "THRICE DAILY": FrequencySchedule(count_per_day=3, times=["09:00", "14:00", "21:00"], abbreviation="TID"),
    "3X/DAY": FrequencySchedule(count_per_day=3, times=["09:00", "14:00", "21:00"], abbreviation="TID"),
    
    # Four times daily
    "QID": FrequencySchedule(count_per_day=4, times=["09:00", "13:00", "17:00", "21:00"], abbreviation="QID"),
    "4X/DAY": FrequencySchedule(count_per_day=4, times=["09:00", "13:00", "17:00", "21:00"], abbreviation="QID"),
    
    # Bedtime
    "QHS": FrequencySchedule(count_per_day=1, times=["22:00"], abbreviation="QHS"),
    "HS": FrequencySchedule(count_per_day=1, times=["22:00"], abbreviation="QHS"),
    "BEDTIME": FrequencySchedule(count_per_day=1, times=["22:00"], abbreviation="QHS"),
    "AT NIGHT": FrequencySchedule(count_per_day=1, times=["22:00"], abbreviation="QHS"),
    
    # Morning
    "QAM": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="QAM"),
    "MORNING": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="QAM"),
    
    # Indian notation (morning-afternoon-night)
    "1-0-1": FrequencySchedule(count_per_day=2, times=["09:00", "21:00"], abbreviation="1-0-1"),
    "1-1-1": FrequencySchedule(count_per_day=3, times=["09:00", "14:00", "21:00"], abbreviation="1-1-1"),
    "1-0-0": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="1-0-0"),
    "0-0-1": FrequencySchedule(count_per_day=1, times=["21:00"], abbreviation="0-0-1"),
    "0-1-0": FrequencySchedule(count_per_day=1, times=["14:00"], abbreviation="0-1-0"),
    "2-0-0": FrequencySchedule(count_per_day=1, times=["09:00"], abbreviation="2-0-0"),  # 2 pills in morning
    "1-1-0": FrequencySchedule(count_per_day=2, times=["09:00", "14:00"], abbreviation="1-1-0"),
    "0-1-1": FrequencySchedule(count_per_day=2, times=["14:00", "21:00"], abbreviation="0-1-1"),
    
    # Every X hours
    "Q4H": FrequencySchedule(count_per_day=6, times=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"], abbreviation="Q4H"),
    "Q6H": FrequencySchedule(count_per_day=4, times=["00:00", "06:00", "12:00", "18:00"], abbreviation="Q6H"),
    "Q8H": FrequencySchedule(count_per_day=3, times=["08:00", "16:00", "00:00"], abbreviation="Q8H"),
    "Q12H": FrequencySchedule(count_per_day=2, times=["08:00", "20:00"], abbreviation="Q12H"),
    
    # As needed
    "PRN": FrequencySchedule(count_per_day=0, times=[], abbreviation="PRN"),
    "AS NEEDED": FrequencySchedule(count_per_day=0, times=[], abbreviation="PRN"),
    "SOS": FrequencySchedule(count_per_day=0, times=[], abbreviation="PRN"),
}


class SemanticParser:
    """Parser for medical prescription semantics"""
    
    def parse_frequency(self, frequency_text: str) -> Optional[FrequencySchedule]:
        """
        Parse frequency text into structured schedule
        
        Args:
            frequency_text: Raw frequency string from prescription
            
        Returns:
            FrequencySchedule or None if not recognized
            
        Example:
            >>> parser.parse_frequency("BID")
            FrequencySchedule(count_per_day=2, times=["09:00", "21:00"], abbreviation="BID")
            >>> parser.parse_frequency("1-0-1")
            FrequencySchedule(count_per_day=2, times=["09:00", "21:00"], abbreviation="1-0-1")
        """
        if not frequency_text:
            return None
        
        # Normalize input
        normalized = frequency_text.upper().strip()
        
        # Direct lookup
        if normalized in FREQUENCY_MAP:
            logger.info(f"✅ Parsed frequency: {frequency_text} → {FREQUENCY_MAP[normalized].abbreviation}")
            return FREQUENCY_MAP[normalized]
        
        # Try fuzzy matching for common variations
        for key, schedule in FREQUENCY_MAP.items():
            if key in normalized or normalized in key:
                logger.info(f"✅ Fuzzy matched frequency: {frequency_text} → {schedule.abbreviation}")
                return schedule
        
        logger.warning(f"⚠️  Unrecognized frequency: {frequency_text}")
        return None
    
    def calculate_total_inventory(self, 
                                  dosage_per_intake: int,
                                  frequency: FrequencySchedule,
                                  duration_days: int) -> int:
        """
        Calculate total pills needed for prescription
        
        Args:
            dosage_per_intake: Number of pills per dose (e.g., 1 or 2)
            frequency: Parsed frequency schedule
            duration_days: Treatment duration in days
            
        Returns:
            Total number of pills required
            
        Example:
            >>> schedule = parser.parse_frequency("BID")
            >>> parser.calculate_total_inventory(1, schedule, 10)
            20  # 1 pill × 2 times/day × 10 days
        """
        if frequency.count_per_day == 0:  # PRN
            # For PRN, estimate 1 dose per day as baseline
            return dosage_per_intake * duration_days
        
        total = dosage_per_intake * frequency.count_per_day * duration_days
        logger.info(
            f"📊 Inventory calculation: {dosage_per_intake} pills × "
            f"{frequency.count_per_day} times/day × {duration_days} days = {total} pills"
        )
        return total
    
    def extract_dosage_from_text(self, dosage_text: str) -> int:
        """
        Extract numeric dosage from text
        
        Args:
            dosage_text: Dosage string (e.g., "1 tablet", "2 pills", "500mg")
            
        Returns:
            Numeric dosage count (defaults to 1 if unclear)
        """
        import re
        
        # Look for numbers at start of string
        match = re.search(r'^(\d+)', dosage_text.strip())
        if match:
            return int(match.group(1))
        
        # Common words
        if "one" in dosage_text.lower():
            return 1
        if "two" in dosage_text.lower():
            return 2
        if "three" in dosage_text.lower():
            return 3
        
        # Default to 1
        return 1


# Global parser instance
semantic_parser = SemanticParser()


def get_semantic_parser() -> SemanticParser:
    """Get the global semantic parser instance"""
    return semantic_parser
