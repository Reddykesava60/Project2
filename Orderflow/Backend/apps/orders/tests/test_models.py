"""
Tests for Orders model and API.
"""
import pytest
from apps.orders.models import Order, OrderItem, DailyOrderSequence
from django.utils import timezone


@pytest.mark.unit
class TestOrderModel:
    """Test Order model functionality."""
    
    def test_order_creation(self, restaurant, menu_item):
        """Test creating an order."""
        order = Order.objects.create(
            restaurant=restaurant,
            order_number='A1',
            daily_sequence=1,
            customer_name='Test Customer',
            subtotal=499.00,
            tax=39.92,
            total_amount=538.92,
            payment_method='CASH',
            status='AWAITING_PAYMENT'
        )
        assert order.order_number == 'A1'
        assert order.status == 'AWAITING_PAYMENT'
    
    def test_order_status_transitions(self, restaurant):
        """Test valid order status transitions."""
        order = Order.objects.create(
            restaurant=restaurant,
            order_number='A1',
            daily_sequence=1,
            subtotal=100,
            tax=8,
            total_amount=108,
            status='PENDING'
        )
        
        # Valid transitions
        assert order.can_transition_to('PREPARING')
        assert order.can_transition_to('CANCELLED')
        
        # Invalid transition
        assert not order.can_transition_to('COMPLETED')
    
    def test_daily_sequence_generation(self, restaurant):
        """Test atomic sequence number generation."""
        seq1 = DailyOrderSequence.get_next_sequence(restaurant)
        seq2 = DailyOrderSequence.get_next_sequence(restaurant)
        seq3 = DailyOrderSequence.get_next_sequence(restaurant)
        
        assert seq1 == 1
        assert seq2 == 2
        assert seq3 == 3
    
    def test_analytics_fields_set_on_creation(self, restaurant):
        """Test that hour/day fields are set automatically."""
        order = Order.objects.create(
            restaurant=restaurant,
            order_number='A1',
            daily_sequence=1,
            subtotal=100,
            tax=8,
            total_amount=108
        )
        
        now = timezone.now()
        assert order.hour_of_day == now.hour
        assert order.day_of_week == now.weekday()


@pytest.mark.integration
class TestOrderAPI:
    """Test order management API."""
    
    def test_list_orders_requires_auth(self, api_client):
        """Test that listing orders requires authentication."""
        response = api_client.get('/api/orders/')
        assert response.status_code == 401
    
    def test_staff_can_view_restaurant_orders(
        self, staff_client, restaurant, menu_item
    ):
        """Test staff can view their restaurant's orders."""
        # Create test order
        order = Order.objects.create(
            restaurant=restaurant,
            order_number='A1',
            daily_sequence=1,
            subtotal=499.00,
            tax=39.92,
            total_amount=538.92
        )
        
        response = staff_client.get('/api/orders/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
