"""
Payment service for Razorpay integration.
Handles order creation, payment verification, and webhooks.
"""

import hmac
import hashlib
import json
import logging
from decimal import Decimal
from typing import Optional, Tuple

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


class PaymentServiceError(Exception):
    """Base exception for payment service errors."""
    pass


class PaymentVerificationError(PaymentServiceError):
    """Raised when payment verification fails."""
    pass


class RazorpayService:
    """
    Razorpay payment integration service.
    
    Usage:
        service = RazorpayService()
        order_data = service.create_order(amount=10000, currency='INR', order_id='ORD-123')
        is_valid = service.verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    """
    
    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        self.webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)
        self._client = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Razorpay credentials are configured."""
        return bool(self.key_id and self.key_secret)
    
    @property
    def client(self):
        """Lazy-load Razorpay client."""
        if self._client is None:
            if not self.is_configured:
                raise PaymentServiceError(
                    "Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."
                )
            try:
                import razorpay
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except ImportError:
                raise PaymentServiceError(
                    "razorpay package not installed. Run: pip install razorpay"
                )
        return self._client
    
    def create_order(
        self,
        amount: int,  # Amount in paise (smallest currency unit)
        currency: str = 'INR',
        receipt: str = None,
        notes: dict = None
    ) -> dict:
        """
        Create a Razorpay order.
        
        Args:
            amount: Amount in paise (e.g., 10000 for ₹100)
            currency: Currency code (default INR)
            receipt: Your internal order ID
            notes: Additional metadata
            
        Returns:
            Razorpay order object with 'id', 'amount', 'currency', etc.
        """
        # Check for simulation mode (RAZORPAY_FORCE_SUCCESS)
        from django.conf import settings
        force_success = getattr(settings, 'RAZORPAY_FORCE_SUCCESS', False)
        
        if force_success:
            # Simulation mode: return a fake Razorpay order
            import uuid
            fake_order_id = f"order_sim_{uuid.uuid4().hex[:16]}"
            logger.info(f"[SIMULATION] Created fake Razorpay order: {fake_order_id}")
            return {
                'id': fake_order_id,
                'amount': amount,
                'currency': currency,
                'receipt': receipt,
                'notes': notes or {},
                'status': 'created',
            }
        
        try:
            order_data = {
                'amount': amount,
                'currency': currency,
                'receipt': receipt,
                'notes': notes or {},
            }
            
            order = self.client.order.create(data=order_data)
            logger.info(f"Created Razorpay order: {order['id']} for receipt: {receipt}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            raise PaymentServiceError(f"Failed to create payment order: {e}")
    
    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature using the official Razorpay SDK.
        
        This is the CRITICAL step that ensures payment was actually successful.
        Never trust client-side payment success without this verification.
        
        The SDK's client.utility.verify_payment_signature() performs:
        1. Constructs the message: "{order_id}|{payment_id}"
        2. Computes HMAC-SHA256 with the key_secret
        3. Timing-safe comparison with the provided signature
        4. Raises SignatureVerificationError if verification fails
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            
        Returns:
            True if signature is valid
            
        Raises:
            PaymentVerificationError if signature is invalid
        """
        from django.conf import settings
        from razorpay.errors import SignatureVerificationError
        
        # Check if we're in simulation mode (for testing only - NEVER in production)
        force_success = getattr(settings, 'RAZORPAY_FORCE_SUCCESS', False)
        live_mode = getattr(settings, 'RAZORPAY_LIVE_MODE', True)  # Default to LIVE for safety
        
        if force_success and not live_mode:
            # Simulation mode: accept any signature for testing
            logger.warning(
                f"[SIMULATION] Skipping signature verification for payment: {razorpay_payment_id}. "
                "NEVER enable RAZORPAY_FORCE_SUCCESS in production!"
            )
            return True
        
        try:
            # Use the official Razorpay SDK for cryptographic verification
            # This is the ONLY trusted way to verify payment authenticity
            params = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            }
            
            # SDK's verify_payment_signature raises SignatureVerificationError if invalid
            self.client.utility.verify_payment_signature(params)
            
            logger.info(f"Payment cryptographically verified via SDK: {razorpay_payment_id}")
            return True
            
        except SignatureVerificationError as e:
            logger.warning(
                f"Payment signature verification FAILED: {razorpay_payment_id}. "
                f"Order: {razorpay_order_id}. Error: {e}"
            )
            raise PaymentVerificationError("Invalid payment signature - payment not verified by Razorpay")
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            raise PaymentVerificationError(f"Verification failed: {e}")
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature using the official Razorpay SDK.
        
        Webhooks must be verified to ensure they are genuinely from Razorpay.
        This uses client.utility.verify_webhook_signature() from the SDK.
        
        Args:
            body: Raw request body bytes
            signature: X-Razorpay-Signature header value
            
        Returns:
            True if signature is valid
            
        Raises:
            PaymentVerificationError if signature is invalid
        """
        from django.conf import settings
        from razorpay.errors import SignatureVerificationError
        
        if not self.webhook_secret:
            raise PaymentServiceError("Webhook secret not configured (RAZORPAY_WEBHOOK_SECRET)")
        
        # Check if we're in simulation mode
        force_success = getattr(settings, 'RAZORPAY_FORCE_SUCCESS', False)
        live_mode = getattr(settings, 'RAZORPAY_LIVE_MODE', True)
        
        if force_success and not live_mode:
            logger.warning("[SIMULATION] Skipping webhook signature verification")
            return True
        
        try:
            # Convert body to string if bytes (SDK expects string)
            body_str = body.decode('utf-8') if isinstance(body, bytes) else body
            
            # Use SDK's verify_webhook_signature for cryptographic verification
            self.client.utility.verify_webhook_signature(
                body_str,
                signature,
                self.webhook_secret
            )
            logger.info("Webhook signature verified via SDK")
            return True
            
        except SignatureVerificationError as e:
            logger.warning(f"Webhook signature verification FAILED: {e}")
            raise PaymentVerificationError("Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            raise PaymentVerificationError(f"Webhook verification failed: {e}")
    
    def fetch_payment(self, payment_id: str) -> dict:
        """
        Fetch payment details from Razorpay.
        
        Args:
            payment_id: Razorpay payment ID
            
        Returns:
            Payment details dict
        """
        try:
            return self.client.payment.fetch(payment_id)
        except Exception as e:
            logger.error(f"Failed to fetch payment {payment_id}: {e}")
            raise PaymentServiceError(f"Failed to fetch payment: {e}")
    
    def capture_payment(self, payment_id: str, amount: int) -> dict:
        """
        Capture an authorized payment.
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture in paise
            
        Returns:
            Captured payment details
        """
        try:
            return self.client.payment.capture(payment_id, amount)
        except Exception as e:
            logger.error(f"Failed to capture payment {payment_id}: {e}")
            raise PaymentServiceError(f"Failed to capture payment: {e}")
    
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None,
        notes: dict = None
    ) -> dict:
        """
        Refund a payment (full or partial).
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund in paise (None for full refund)
            notes: Refund notes/metadata
            
        Returns:
            Refund details dict
        """
        try:
            refund_data = {'notes': notes or {}}
            if amount is not None:
                refund_data['amount'] = amount
            
            refund = self.client.payment.refund(payment_id, refund_data)
            logger.info(f"Refund created: {refund['id']} for payment: {payment_id}")
            return refund
            
        except Exception as e:
            logger.error(f"Failed to refund payment {payment_id}: {e}")
            raise PaymentServiceError(f"Failed to process refund: {e}")


# Singleton instance
razorpay_service = RazorpayService()


def process_order_payment(order, razorpay_payment_id: str, razorpay_order_id: str, razorpay_signature: str) -> Tuple[bool, str]:
    """
    Process and verify payment for an order.
    
    Args:
        order: Order model instance
        razorpay_payment_id: Payment ID from Razorpay
        razorpay_order_id: Order ID from Razorpay  
        razorpay_signature: Signature from Razorpay
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # ALWAYS verify the payment signature via the service.
        # The service internally handles RAZORPAY_LIVE_MODE and RAZORPAY_FORCE_SUCCESS.
        # This ensures a single source of truth for payment verification.
        razorpay_service.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        # Update order atomically
        with transaction.atomic():
            order.refresh_from_db()
            order.payment_id = razorpay_payment_id
            order.payment_status = 'success'  # Lowercase per PRD
            # Payment confirmed -> preparing
            # Historically some flows used AWAITING_PAYMENT; treat both as unpaid.
            if order.status in ('pending', 'PENDING', 'AWAITING_PAYMENT'):
                order.status = 'preparing'  # Lowercase per PRD
            order.save(update_fields=[
                'payment_id', 'payment_status', 'status', 'updated_at', 'version'
            ])
        
        return True, "Payment verified successfully"
        
    except PaymentVerificationError as e:
        logger.warning(f"Payment verification failed for order {order.id}: {e}")
        
        with transaction.atomic():
            order.refresh_from_db()
            order.payment_status = 'failed'  # Lowercase
            order.status = 'failed'  # Mark order as failed
            order.save(update_fields=['payment_status', 'status', 'updated_at', 'version'])
        
        return False, str(e)
        
    except Exception as e:
        logger.error(f"Unexpected error processing payment for order {order.id}: {e}")
        return False, f"Payment processing error: {e}"
