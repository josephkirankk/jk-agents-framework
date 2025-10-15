"""
Visiting Card Extraction Tools for JK Agents
============================================

Helper tools for visiting card data extraction, normalization, and validation.
These tools work in-process with the agent framework.
"""

import re
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool

# Try to import optional dependencies
try:
    import phonenumbers
    HAS_PHONENUMBERS = True
except ImportError:
    HAS_PHONENUMBERS = False

try:
    import dns.resolver
    HAS_DNS = False  # Disabled by default for reliability
except ImportError:
    HAS_DNS = False


# =============================================================================
# Phone Number Normalization
# =============================================================================

@tool
def normalize_phone(phone: str, country_hint: Optional[str] = None) -> Dict[str, Any]:
    """Normalize phone number to E.164 format and validate.
    
    Args:
        phone: Raw phone number string (e.g., "(555) 123-4567", "+1-555-123-4567")
        country_hint: Optional country code hint (e.g., "US", "IN", "GB")
    
    Returns:
        Dictionary with normalized phone data including:
        - original: Original input
        - e164: E.164 formatted number (e.g., "+15551234567")
        - country: Detected country code
        - valid: Boolean indicating if number is valid
        - type: Detected type (mobile, fixed_line, etc.) if available
        - error: Error message if parsing failed
    """
    result = {
        "original": phone,
        "e164": None,
        "country": None,
        "valid": False,
        "type": "unknown",
        "error": None
    }
    
    if not phone or not phone.strip():
        result["error"] = "Empty phone number"
        return result
    
    # If phonenumbers library not available, do basic normalization
    if not HAS_PHONENUMBERS:
        # Basic cleanup: remove common separators
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone.strip())
        # If starts with + or contains only digits, consider it valid
        if cleaned.startswith('+') and cleaned[1:].isdigit():
            result["e164"] = cleaned
            result["valid"] = True
        elif cleaned.isdigit() and len(cleaned) >= 10:
            result["e164"] = f"+{cleaned}"
            result["valid"] = True
        else:
            result["error"] = "phonenumbers library not installed for advanced parsing"
        return result
    
    # Use phonenumbers library for proper parsing
    try:
        parsed = phonenumbers.parse(phone, country_hint)
        result["valid"] = phonenumbers.is_valid_number(parsed)
        result["e164"] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        result["country"] = phonenumbers.region_code_for_number(parsed)
        
        # Detect number type
        number_type = phonenumbers.number_type(parsed)
        type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
            phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
            phonenumbers.PhoneNumberType.VOIP: "voip",
        }
        result["type"] = type_map.get(number_type, "unknown")
        
    except phonenumbers.NumberParseException as e:
        result["error"] = f"Parse error: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
    
    return result


# =============================================================================
# Email Validation
# =============================================================================

@tool
def validate_email(email: str, check_mx: bool = False) -> Dict[str, Any]:
    """Validate email address format and optionally check MX records.
    
    Args:
        email: Email address to validate
        check_mx: Whether to check MX records (requires dns.resolver, disabled by default)
    
    Returns:
        Dictionary with validation results:
        - email: Original input
        - format_valid: Boolean indicating if format is valid
        - mx_valid: Boolean indicating if MX records exist (None if not checked)
        - domain: Extracted domain
        - verified: Overall verification status
        - error: Error message if validation failed
    """
    result = {
        "email": email,
        "format_valid": False,
        "mx_valid": None,
        "domain": None,
        "verified": False,
        "error": None
    }
    
    if not email or not email.strip():
        result["error"] = "Empty email address"
        return result
    
    email = email.strip().lower()
    result["email"] = email
    
    # RFC 5322 simplified email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        result["error"] = "Invalid email format"
        return result
    
    result["format_valid"] = True
    result["domain"] = email.split('@')[-1]
    
    # MX record check (optional, requires DNS library)
    if check_mx and HAS_DNS:
        try:
            answers = dns.resolver.resolve(result["domain"], 'MX', lifetime=5.0)
            result["mx_valid"] = len(answers) > 0
        except dns.resolver.NXDOMAIN:
            result["mx_valid"] = False
            result["error"] = "Domain does not exist"
        except dns.resolver.NoAnswer:
            result["mx_valid"] = False
            result["error"] = "No MX records found"
        except dns.resolver.Timeout:
            result["mx_valid"] = None
            result["error"] = "DNS timeout"
        except Exception as e:
            result["mx_valid"] = None
            result["error"] = f"DNS check error: {str(e)}"
    
    # Overall verification
    if check_mx and result["mx_valid"] is not None:
        result["verified"] = result["format_valid"] and result["mx_valid"]
    else:
        result["verified"] = result["format_valid"]
    
    return result


# =============================================================================
# URL Parsing and Validation
# =============================================================================

@tool
def parse_url(url: str) -> Dict[str, Any]:
    """Parse and validate URL from visiting card.
    
    Args:
        url: URL string to parse
    
    Returns:
        Dictionary with parsed URL components:
        - original: Original input
        - normalized: Normalized URL with protocol
        - domain: Extracted domain
        - protocol: Detected protocol (http/https)
        - valid: Boolean indicating if URL is valid
        - error: Error message if parsing failed
    """
    result = {
        "original": url,
        "normalized": None,
        "domain": None,
        "protocol": None,
        "valid": False,
        "error": None
    }
    
    if not url or not url.strip():
        result["error"] = "Empty URL"
        return result
    
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Basic URL validation
    url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    
    if not re.match(url_pattern, url):
        result["error"] = "Invalid URL format"
        return result
    
    result["normalized"] = url
    result["valid"] = True
    result["protocol"] = "https" if url.startswith("https://") else "http"
    
    # Extract domain
    match = re.search(r'https?://([a-zA-Z0-9.-]+)', url)
    if match:
        result["domain"] = match.group(1)
    
    return result


# =============================================================================
# Company Name Normalization
# =============================================================================

@tool
def normalize_company_name(company_name: str) -> Dict[str, Any]:
    """Normalize company name for research queries.
    
    Args:
        company_name: Raw company name from OCR or logo detection
    
    Returns:
        Dictionary with normalized company name:
        - original: Original input
        - normalized: Cleaned company name
        - search_variants: List of search query variants
        - legal_suffixes: Detected legal suffixes (LLC, Inc, Ltd, etc.)
    """
    result = {
        "original": company_name,
        "normalized": None,
        "search_variants": [],
        "legal_suffixes": []
    }
    
    if not company_name or not company_name.strip():
        return result
    
    name = company_name.strip()
    
    # Common legal suffixes
    suffixes = [
        'LLC', 'L.L.C.', 'Inc', 'Inc.', 'Incorporated',
        'Ltd', 'Ltd.', 'Limited', 'Corp', 'Corp.', 'Corporation',
        'Co', 'Co.', 'Company', 'LLP', 'L.L.P.', 'PLC', 'P.L.C.',
        'GmbH', 'AG', 'SA', 'S.A.', 'SAS', 'SARL', 'Pvt', 'Pvt.',
        'Private Limited', 'Pty', 'Pty.', 'N.V.', 'B.V.'
    ]
    
    # Detect and extract suffixes
    name_parts = name
    for suffix in suffixes:
        pattern = rf'\b{re.escape(suffix)}\b\.?$'
        if re.search(pattern, name_parts, re.IGNORECASE):
            result["legal_suffixes"].append(suffix)
            name_parts = re.sub(pattern, '', name_parts, flags=re.IGNORECASE).strip()
    
    # Clean up trailing punctuation (commas, periods)
    name_parts = re.sub(r'[,.\s]+$', '', name_parts).strip()
    
    result["normalized"] = name_parts
    
    # Generate search variants
    result["search_variants"] = [
        result["normalized"],  # Without suffix
        name,  # With suffix
        f'"{result["normalized"]}"',  # Quoted for exact match
    ]
    
    # Add domain-style variant if applicable
    domain_safe = result["normalized"].lower().replace(' ', '')
    if domain_safe:
        result["search_variants"].append(f"{domain_safe} company")
    
    return result


# =============================================================================
# Data Extraction Helper
# =============================================================================

@tool
def extract_contact_fields(ocr_text: str) -> Dict[str, Any]:
    """Extract common contact fields from OCR text using regex patterns.
    
    Args:
        ocr_text: Raw OCR text from visiting card
    
    Returns:
        Dictionary with extracted fields:
        - phones: List of detected phone numbers
        - emails: List of detected email addresses
        - urls: List of detected URLs/websites
        - potential_names: List of potential person names
        - addresses: List of potential addresses
    """
    result = {
        "phones": [],
        "emails": [],
        "urls": [],
        "potential_names": [],
        "addresses": []
    }
    
    if not ocr_text:
        return result
    
    # Extract phone numbers (various formats)
    phone_patterns = [
        r'\+?\d{1,3}[\s\-\.]?\(?\d{2,4}\)?[\s\-\.]?\d{3,4}[\s\-\.]?\d{3,4}',  # International
        r'\(\d{3}\)\s?\d{3}[\-\.]?\d{4}',  # (555) 123-4567
        r'\d{3}[\-\.\s]\d{3}[\-\.\s]\d{4}',  # 555-123-4567
        r'\d{10,}',  # 10+ digits
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, ocr_text)
        result["phones"].extend(matches)
    
    # Remove duplicates
    result["phones"] = list(set(result["phones"]))
    
    # Extract emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    result["emails"] = list(set(re.findall(email_pattern, ocr_text)))
    
    # Extract URLs
    url_patterns = [
        r'https?://[^\s]+',  # Full URLs
        r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # www.example.com
        r'\b[a-zA-Z0-9.-]+\.(?:com|org|net|edu|gov|co|io|ai)\b',  # Common TLDs
    ]
    
    for pattern in url_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        result["urls"].extend(matches)
    
    result["urls"] = list(set(result["urls"]))
    
    # Extract potential names (lines with 2-4 words, title case, no numbers)
    lines = ocr_text.split('\n')
    for line in lines:
        line = line.strip()
        words = line.split()
        if 2 <= len(words) <= 4 and not any(char.isdigit() for char in line):
            if any(word[0].isupper() for word in words if word):
                result["potential_names"].append(line)
    
    return result


# =============================================================================
# Tool Registry
# =============================================================================

def get_all_visiting_card_tools():
    """Get all visiting card extraction tools.
    
    Returns:
        List of LangChain tools for visiting card processing
    """
    return [
        normalize_phone,
        validate_email,
        parse_url,
        normalize_company_name,
        extract_contact_fields
    ]


def get_tool_by_name(tool_name: str):
    """Get a specific visiting card tool by name.
    
    Args:
        tool_name: Name of the tool to retrieve
    
    Returns:
        The requested tool or None if not found
    """
    tool_map = {
        "normalize_phone": normalize_phone,
        "validate_email": validate_email,
        "parse_url": parse_url,
        "normalize_company_name": normalize_company_name,
        "extract_contact_fields": extract_contact_fields,
    }
    return tool_map.get(tool_name)
