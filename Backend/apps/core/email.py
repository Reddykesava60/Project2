"""
Email utility functions for DineFlow2.
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def send_template_email(
    subject: str,
    template_name: str,
    context: dict,
    recipient_list: List[str],
    from_email: Optional[str] = None,
    html_template_name: Optional[str] = None
) -> bool:
    """
    Send an email using Django templates.
    
    Args:
        subject: Email subject
        template_name: Path to text template (e.g., 'emails/order_confirmation.txt')
        context: Template context data
        recipient_list: List of recipient email addresses
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        html_template_name: Optional HTML template path
    
    Returns:
        bool: True if email sent successfully
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    
    try:
        # Render text content
        text_content = render_to_string(template_name, context)
        
        if html_template_name:
            # Send multipart email with HTML
            html_content = render_to_string(html_template_name, context)
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=recipient_list
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        else:
            # Send text-only email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False
            )
        
        logger.info(f"Email sent: {subject} to {recipient_list}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {subject} to {recipient_list}. Error: {e}")
        return False


def send_bulk_emails(emails: List[dict]) -> int:
    """
    Send multiple emails in batch.
    
    Args:
        emails: List of email dictionaries with keys:
            - subject, template_name, context, recipient_list
    
    Returns:
        int: Number of emails sent successfully
    """
    sent_count = 0
    for email_data in emails:
        if send_template_email(**email_data):
            sent_count += 1
    return sent_count
