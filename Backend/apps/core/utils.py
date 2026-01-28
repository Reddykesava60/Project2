"""
Utility functions for the DineFlow2 application.
"""

import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from django.conf import settings


def generate_qr_signature(restaurant_id: str, qr_version: int, qr_secret: str, timestamp: str = None) -> str:
    """
    Generate HMAC signature for QR code validation.
    
    Args:
        restaurant_id: UUID of the restaurant
        qr_version: Version number of the QR code
        qr_secret: Restaurant-specific secret for HMAC
        timestamp: Optional timestamp string (uses current time if not provided)
    
    Returns:
        Base64-encoded HMAC signature
    """
    if timestamp is None:
        timestamp = datetime.utcnow().strftime('%Y%m%d')
    
    message = f"{restaurant_id}:{qr_version}:{timestamp}"
    signature = hmac.new(
        qr_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    
    return base64.urlsafe_b64encode(signature).decode()[:32]


def verify_qr_signature(restaurant_id: str, qr_version: int, signature: str, qr_secret: str, max_age_days: int = 365) -> bool:
    """
    Verify HMAC signature from QR code.
    
    Args:
        restaurant_id: UUID of the restaurant
        qr_version: Version number of the QR code
        signature: The signature to verify
        qr_secret: Restaurant-specific secret for HMAC
        max_age_days: Maximum age of QR code in days (default 365)
    
    Returns:
        True if signature is valid, False otherwise
    """
    # Check signature for each day in the valid range
    for days_ago in range(max_age_days):
        timestamp = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y%m%d')
        expected = generate_qr_signature(restaurant_id, qr_version, qr_secret, timestamp)
        if hmac.compare_digest(signature, expected):
            return True
    
    return False


def generate_order_number(daily_sequence: int) -> str:
    """
    Generate human-readable order number from daily sequence.
    Format: A1, A2, ..., A99, B1, B2, ..., Z99
    
    Args:
        daily_sequence: Sequential order number for the day (1-based)
    
    Returns:
        Human-readable order number like "A24" or "B15"
    """
    if daily_sequence < 1:
        raise ValueError("Daily sequence must be positive")
    
    # Each letter covers 99 orders
    letter_index = (daily_sequence - 1) // 99
    number = ((daily_sequence - 1) % 99) + 1
    
    # Use letters A-Z (26 letters * 99 = 2574 orders per day max)
    if letter_index >= 26:
        letter_index = letter_index % 26
    
    letter = chr(ord('A') + letter_index)
    return f"{letter}{number}"


def calculate_order_totals(items: list, tax_rate: float = 0.08) -> dict:
    """
    Calculate order subtotal, tax, and total.
    
    Args:
        items: List of order items with 'quantity' and 'price_at_order' fields
        tax_rate: Tax rate as decimal (default 8%)
    
    Returns:
        Dict with subtotal, tax, and total amounts
    """
    subtotal = sum(item['quantity'] * item['price_at_order'] for item in items)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    
    return {
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    }


# Import timedelta for verify_qr_signature
from datetime import timedelta


def parse_qr_token(qr_token: str) -> dict:
    """
    Parse QR token string into components.
    
    QR token format: base64(restaurant_id:qr_version:timestamp:signature)
    or JSON: {"r": "restaurant_id", "v": qr_version, "t": timestamp, "s": signature}
    
    Args:
        qr_token: The QR token string from frontend
    
    Returns:
        Dict with restaurant_id, qr_version, timestamp, signature
    """
    import json
    import base64
    
    try:
        # Try JSON format first
        data = json.loads(qr_token)
        return {
            'restaurant_id': data.get('r') or data.get('restaurant_id'),
            'qr_version': data.get('v') or data.get('qr_version'),
            'timestamp': data.get('t') or data.get('timestamp'),
            'signature': data.get('s') or data.get('signature'),
        }
    except (json.JSONDecodeError, TypeError):
        # Try base64 encoded format
        try:
            decoded = base64.urlsafe_b64decode(qr_token + '==').decode('utf-8')
            parts = decoded.split(':')
            if len(parts) >= 4:
                return {
                    'restaurant_id': parts[0],
                    'qr_version': int(parts[1]),
                    'timestamp': parts[2],
                    'signature': parts[3],
                }
        except Exception:
            pass
    
    # Fallback: assume it's just the order ID (for backward compatibility)
    return {
        'order_id': qr_token,
    }
