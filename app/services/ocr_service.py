"""
OCR Service with Image Preprocessing
Extracts text from prescription images using OpenCV + Tesseract.
"""
import cv2
import numpy as np
import pytesseract
from typing import Optional, Dict, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class OCRService:
    """OCR service with advanced image preprocessing"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR service
        
        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        logger.info("✅ OCR Service initialized")
    
    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess prescription image for optimal OCR
        
        Steps:
        1. Decode image
        2. Grayscale conversion
        3. Noise reduction (bilateral filter)
        4. Deskewing (rotation correction)
        5. Contrast enhancement (CLAHE)
        6. Adaptive thresholding
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Preprocessed image as numpy array
        """
        # 1. Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        # 2. Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 3. Noise reduction - bilateral filter preserves edges
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 4. Deskewing
        deskewed = self._deskew(denoised)
        
        # 5. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(deskewed)
        
        # 6. Adaptive thresholding
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        logger.info("✅ Image preprocessing complete")
        return binary
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Correct image rotation using Hough Line Transform
        
        Args:
            image: Grayscale image
            
        Returns:
            Deskewed image
        """
        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None or len(lines) == 0:
            return image  # No lines detected, return original
        
        # Calculate median angle
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            angles.append(angle)
        
        median_angle = np.median(angles)
        
        # Only deskew if angle is significant (> 0.5 degrees)
        if abs(median_angle) < 0.5:
            return image
        
        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), 
                                 flags=cv2.INTER_CUBIC, 
                                 borderMode=cv2.BORDER_REPLICATE)
        
        logger.info(f"🔄 Deskewed image by {median_angle:.2f} degrees")
        return rotated
    
    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from prescription image
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text
        """
        # Preprocess image
        preprocessed = self.preprocess_image(image_bytes)
        
        # Run Tesseract OCR
        text = pytesseract.image_to_string(
            preprocessed,
            lang='eng',
            config='--psm 6'  # Assume uniform block of text
        )
        
        logger.info(f"📄 Extracted {len(text)} characters")
        return text
    
    def extract_structured_data(self, text: str) -> Dict:
        """
        Extract structured fields from OCR text using regex
        
        Extracts:
        - Pharmacy name/phone
        - Doctor name
        - Medications (drug, strength, frequency, duration)
        
        Args:
            text: Raw OCR text
            
        Returns:
            Structured data dictionary
        """
        result = {
            "pharmacy_name": None,
            "pharmacy_phone": None,
            "doctor_name": None,
            "prescription_date": None,
            "medications": []
        }
        
        lines = text.split('\n')
        
        # Extract pharmacy info (usually at top)
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            # Phone pattern: 10-digit number
            phone_match = re.search(r'(\d{10}|\d{3}[-.\s]\d{3}[-.\s]\d{4})', line)
            if phone_match and not result["pharmacy_phone"]:
                result["pharmacy_phone"] = phone_match.group(1)
                # Pharmacy name is likely on same or previous line
                if i > 0:
                    result["pharmacy_name"] = lines[i-1].strip()
        
        # Extract doctor name (look for "Dr." or "Doctor")
        for line in lines[:10]:
            if re.search(r'\bDr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line, re.IGNORECASE):
                match = re.search(r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line, re.IGNORECASE)
                result["doctor_name"] = match.group(1)
                break
        
        # Extract medications (complex pattern matching)
        # Look for: Drug name + dosage + frequency + duration
        for line in lines:
            # Pattern: Alphanumeric drug name followed by dosage info
            med_match = re.search(
                r'([A-Z][a-z]+(?:[A-Z][a-z]+)*)\s+(\d+\s*mg|\d+\s*mcg)?\s*'
                r'(BID|TID|QD|OD|BD|TD|QHS|\d-\d-\d)?\s*'
                r'(?:for\s+)?(\d+\s*days?)?',
                line,
                re.IGNORECASE
            )
            
            if med_match:
                medication = {
                    "drug_name": med_match.group(1),
                    "strength": med_match.group(2) or "Unknown",
                    "frequency": med_match.group(3) or "QD",
                    "duration": med_match.group(4) or "10 days"
                }
                result["medications"].append(medication)
        
        logger.info(f"📋 Extracted {len(result['medications'])} medications")
        return result


# Global OCR service instance
ocr_service: Optional[OCRService] = None


def init_ocr_service(tesseract_cmd: Optional[str] = None) -> OCRService:
    """Initialize the global OCR service"""
    global ocr_service
    ocr_service = OCRService(tesseract_cmd)
    return ocr_service


def get_ocr_service() -> OCRService:
    """Get the global OCR service instance"""
    if ocr_service is None:
        raise RuntimeError("OCR service not initialized. Call init_ocr_service() first.")
    return ocr_service
