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
        Verify Razorpay payment signature.
        
        This is the CRITICAL step that ensures payment was actually successful.
        Never trust client-side payment success without this verification.
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            
        Returns:
            True if signature is valid
            
        Raises:
            PaymentVerificationError if signature is invalid
        """
        try:
            # Construct the message
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.key_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Timing-safe comparison
            if hmac.compare_digest(expected_signature, razorpay_signature):
                logger.info(f"Payment verified: {razorpay_payment_id}")
                return True
            else:
                logger.warning(f"Payment signature mismatch: {razorpay_payment_id}")
                raise PaymentVerificationError("Invalid payment signature")
                
        except PaymentVerificationError:
            raise
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            raise PaymentVerificationError(f"Verification failed: {e}")
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature.
        
        Args:
            body: Raw request body bytes
            signature: X-Razorpay-Signature header value
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            raise PaymentServiceError("Webhook secret not configured")
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
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
        # In local development/test mode we allow forcing payment success
        # without talking to Razorpay, while keeping the same order state
        # transitions. This is controlled via RAZORPAY_FORCE_SUCCESS and
        # should NEVER be enabled in production.
        force_success = getattr(settings, 'RAZORPAY_FORCE_SUCCESS', False)

        if not force_success:
            # Verify the payment signature against Razorpay
            razorpay_service.verify_payment_signature(
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            )
        
        # Update order atomically
        with transaction.atomic():
            order.refresh_from_db()
            order.payment_id = razorpay_payment_id
            order.payment_status = 'SUCCESS'
            if order.status == 'AWAITING_PAYMENT':
                order.status = 'PREPARING'
            order.save(update_fields=[
                'payment_id', 'payment_status', 'status', 'updated_at', 'version'
            ])
        
        return True, "Payment verified successfully"
        
    except PaymentVerificationError as e:
        logger.warning(f"Payment verification failed for order {order.id}: {e}")
        
        with transaction.atomic():
            order.refresh_from_db()
            order.payment_status = 'FAILED'
            order.status = 'FAILED'
            order.save(update_fields=['payment_status', 'status', 'updated_at', 'version'])
        
        return False, str(e)
        
    except Exception as e:
        logger.error(f"Unexpected error processing payment for order {order.id}: {e}")
        return False, f"Payment processing error: {e}"
