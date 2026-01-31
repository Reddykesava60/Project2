"""
Order-related email notifications.
"""
from apps.core.email import send_template_email
from apps.orders.models import Order
import logging

logger = logging.getLogger(__name__)


def send_order_confirmation(order: Order) -> bool:
    """
    Send order confirmation email to customer.
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if sent successfully
    """
    if not order.customer_name:
        logger.warning(f"Order {order.order_number} has no customer email")
        return False
    
    context = {
        'order': order,
        'restaurant': order.restaurant,
        'items': order.items.all(),
        'order_number': order.order_number,
        'total_amount': order.total_amount,
        'payment_method': order.get_payment_method_display(),
    }
    
    subject = f"Order Confirmation #{order.order_number} - {order.restaurant.name}"
    
    # For now, we'll just log since customer email is not collected
    logger.info(f"Order confirmation for {order.order_number}: {context}")
    return True


def send_order_status_update(order: Order, old_status: str, new_status: str) -> bool:
    """
    Send order status update notification.
    
    Args:
        order: Order instance  
        old_status: Previous status
        new_status: New status
    
    Returns:
        bool: True if sent successfully
    """
    context = {
        'order': order,
        'restaurant': order.restaurant,
        'old_status': order.Status(old_status).label,
        'new_status': order.Status(new_status).label,
        'order_number': order.order_number,
    }
    
    subject = f"Order #{order.order_number} - {order.Status(new_status).label}"
    
    logger.info(f"Order status update for {order.order_number}: {old_status} → {new_status}")
    return True


def send_staff_order_notification(order: Order) -> bool:
    """
    Notify restaurant staff of new order.
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if sent successfully
    """
    # Get restaurant owner and active staff emails
    staff_emails = [order.restaurant.owner.email]
    
    for staff in order.restaurant.staff_members.filter(is_active=True):
        staff_emails.append(staff.user.email)
    
    context = {
        'order': order,
        'restaurant': order.restaurant,
        'items': order.items.all(),
        'order_number': order.order_number,
        'total_amount': order.total_amount,
    }
    
    subject = f"New Order #{order.order_number} - {order.restaurant.name}"
    
    return send_template_email(
        subject=subject,
        template_name='emails/new_order_staff.txt',
        context=context,
        recipient_list=staff_emails,
        html_template_name='emails/new_order_staff.html'
    )
