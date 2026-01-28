"""
End-to-End Validation Script for DineFlow2
Tests real user flows with actual database operations.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import json

from apps.restaurants.models import Restaurant, Staff
from apps.menu.models import MenuCategory, MenuItem
from apps.orders.models import Order, OrderItem, DailyOrderSequence
from apps.core.audit import AuditLog

User = get_user_model()


class E2EValidationTests(TestCase):
    """End-to-end validation tests for real user flows."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create platform admin
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='test123',
            first_name='Admin',
            last_name='User',
            role='platform_admin'
        )
        
        # Create restaurant owner
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='test123',
            first_name='Owner',
            last_name='User',
            role='restaurant_owner'
        )
        
        # Create restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            slug='test-restaurant',
            owner=self.owner,
            status='ACTIVE',
            currency='INR',
            timezone='Asia/Kolkata'
        )
        
        # Create staff
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='test123',
            first_name='Staff',
            last_name='User',
            role='staff',
            restaurant=self.restaurant
        )
        
        self.staff = Staff.objects.create(
            user=self.staff_user,
            restaurant=self.restaurant,
            can_collect_cash=False,
            is_active=True
        )
        
        # Create menu category
        self.category = MenuCategory.objects.create(
            restaurant=self.restaurant,
            name='Main Course',
            is_active=True
        )
        
        # Create menu items
        self.menu_item1 = MenuItem.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name='Burger',
            price=Decimal('150.00'),
            is_available=True,
            is_active=True
        )
        
        self.menu_item2 = MenuItem.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name='Pizza',
            price=Decimal('300.00'),
            is_available=True,
            is_active=True
        )
    
    def test_1_customer_order_flow_cash(self):
        """Test 1: Customer order flow with cash payment."""
        print("\n=== TEST 1: Customer Order Flow (Cash) ===")
        
        # Step 1: Get menu (public endpoint)
        response = self.client.get(f'/api/public/r/{self.restaurant.slug}/menu/')
        self.assertEqual(response.status_code, 200)
        menu_data = response.json()
        self.assertIn('restaurant', menu_data)
        self.assertIn('categories', menu_data)
        print("✓ Menu loaded successfully")
        
        # Step 2: Create order (public endpoint)
        order_data = {
            'customer_name': 'John Doe',
            'payment_method': 'CASH',
            'privacy_accepted': True,
            'items': [
                {'menu_item_id': str(self.menu_item1.id), 'quantity': 2},
                {'menu_item_id': str(self.menu_item2.id), 'quantity': 1},
            ]
        }
        
        response = self.client.post(
            f'/api/public/r/{self.restaurant.slug}/order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        order_response = response.json()
        self.assertTrue(order_response.get('success'))
        order_id = order_response['order']['id']
        order_number = order_response['order']['order_number']
        print(f"✓ Order created: {order_number} (ID: {order_id})")
        
        # Step 3: Verify order in database
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.restaurant, self.restaurant)
        self.assertEqual(order.customer_name, 'John Doe')
        self.assertEqual(order.payment_method, 'CASH')
        self.assertEqual(order.status, 'AWAITING_PAYMENT')
        self.assertEqual(order.items.count(), 2)
        
        # Verify order items
        item1 = order.items.get(menu_item=self.menu_item1)
        self.assertEqual(item1.quantity, 2)
        self.assertEqual(item1.price_at_order, Decimal('150.00'))
        
        item2 = order.items.get(menu_item=self.menu_item2)
        self.assertEqual(item2.quantity, 1)
        self.assertEqual(item2.price_at_order, Decimal('300.00'))
        
        # Verify totals
        expected_subtotal = Decimal('150.00') * 2 + Decimal('300.00') * 1
        self.assertEqual(order.subtotal, expected_subtotal)
        self.assertEqual(order.total_amount, expected_subtotal + order.tax)
        print(f"✓ Order totals correct: Subtotal={order.subtotal}, Tax={order.tax}, Total={order.total_amount}")
        
        # Step 4: Verify order number format (A23)
        self.assertRegex(order.order_number, r'^[A-Z]\d+$')
        print(f"✓ Order number format correct: {order.order_number}")
        
        # Step 5: Verify daily sequence
        self.assertGreater(order.daily_sequence, 0)
        print(f"✓ Daily sequence: {order.daily_sequence}")
        
        # Step 6: Verify audit log
        audit_log = AuditLog.objects.filter(
            entity_id=str(order.id),
            action=AuditLog.Action.ORDER_CREATED
        ).first()
        self.assertIsNotNone(audit_log)
        print(f"✓ Audit log created: {audit_log.action}")
        
        return order
    
    def test_2_customer_order_flow_online(self):
        """Test 2: Customer order flow with online payment."""
        print("\n=== TEST 2: Customer Order Flow (Online) ===")
        
        order_data = {
            'customer_name': 'Jane Smith',
            'payment_method': 'ONLINE',
            'privacy_accepted': True,
            'items': [
                {'menu_item_id': str(self.menu_item1.id), 'quantity': 1},
            ]
        }
        
        response = self.client.post(
            f'/api/public/r/{self.restaurant.slug}/order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        order_response = response.json()
        order_id = order_response['order']['id']
        
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.payment_method, 'ONLINE')
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.payment_status, 'PENDING')
        print(f"✓ Online order created: {order.order_number}")
        
        return order
    
    def test_3_staff_view_active_orders(self):
        """Test 3: Staff can view active orders."""
        print("\n=== TEST 3: Staff View Active Orders ===")
        
        # Create orders
        order1 = self.test_1_customer_order_flow_cash()
        order2 = self.test_2_customer_order_flow_online()
        
        # Login as staff
        refresh = RefreshToken.for_user(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Get active orders
        response = self.client.get(
            f'/api/orders/active/',
            {'restaurant': str(self.restaurant.id)}
        )
        
        self.assertEqual(response.status_code, 200)
        orders_data = response.json()
        self.assertIsInstance(orders_data, list)
        
        order_ids = [o['id'] for o in orders_data]
        self.assertIn(str(order1.id), order_ids)
        self.assertIn(str(order2.id), order_ids)
        print(f"✓ Staff can see {len(orders_data)} active orders")
        
        # Verify order details
        order1_data = next(o for o in orders_data if o['id'] == str(order1.id))
        self.assertEqual(order1_data['order_number'], order1.order_number)
        self.assertEqual(len(order1_data['items']), 2)
        print("✓ Order details match database")
    
    def test_4_staff_cash_permission_enforcement(self):
        """Test 4: Staff cash permission enforcement."""
        print("\n=== TEST 4: Staff Cash Permission Enforcement ===")
        
        # Create order
        order = self.test_1_customer_order_flow_cash()
        
        # Login as staff WITHOUT cash permission
        refresh = RefreshToken.for_user(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Try to collect cash (should fail)
        response = self.client.post(f'/api/orders/{order.id}/cash/')
        self.assertEqual(response.status_code, 403)
        print("✓ Backend rejects cash collection without permission")
        
        # Enable cash permission
        self.staff.can_collect_cash = True
        self.staff.save()
        
        # Now should succeed
        response = self.client.post(f'/api/orders/{order.id}/cash/')
        self.assertEqual(response.status_code, 200)
        
        # Verify payment status updated
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'SUCCESS')
        self.assertEqual(order.cash_collected_by, self.staff_user)
        self.assertIsNotNone(order.cash_collected_at)
        print("✓ Cash collection successful with permission")
        
        # Verify audit log
        audit_log = AuditLog.objects.filter(
            entity_id=str(order.id),
            action=AuditLog.Action.CASH_COLLECTED
        ).first()
        self.assertIsNotNone(audit_log)
        print("✓ Cash collection audited")
    
    def test_5_staff_create_cash_order(self):
        """Test 5: Staff creates cash order."""
        print("\n=== TEST 5: Staff Create Cash Order ===")
        
        # Login as staff with cash permission
        self.staff.can_collect_cash = True
        self.staff.save()
        refresh = RefreshToken.for_user(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create cash order
        order_data = {
            'customer_name': 'Walk-in Customer',
            'items': [
                {'menu_item_id': str(self.menu_item1.id), 'quantity': 1},
            ]
        }
        
        response = self.client.post(
            '/api/orders/staff/create/',
            data=json.dumps(order_data),
            content_type='application/json',
            HTTP_X_RESTAURANT_ID=str(self.restaurant.id)
        )
        
        self.assertEqual(response.status_code, 201)
        order_response = response.json()
        order_id = order_response['id']
        
        # Verify order
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.order_type, 'STAFF_CASH')
        self.assertEqual(order.payment_method, 'CASH')
        self.assertEqual(order.payment_status, 'SUCCESS')
        self.assertEqual(order.created_by, self.staff_user)
        print(f"✓ Staff cash order created: {order.order_number}")
        
        # Verify audit log
        audit_log = AuditLog.objects.filter(
            entity_id=str(order.id),
            action=AuditLog.Action.ORDER_CREATED
        ).first()
        self.assertIsNotNone(audit_log)
        print("✓ Order creation audited")
    
    def test_6_order_completion_flow(self):
        """Test 6: Order completion flow."""
        print("\n=== TEST 6: Order Completion Flow ===")
        
        # Create and pay for order
        order = self.test_1_customer_order_flow_cash()
        self.staff.can_collect_cash = True
        self.staff.save()
        self.staff.can_collect_cash = True
        self.staff.save()
        refresh = RefreshToken.for_user(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Collect payment
        self.client.post(f'/api/orders/{order.id}/cash/')
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'SUCCESS')
        
        # Update status to PREPARING
        response = self.client.post(
            f'/api/orders/{order.id}/update_status/',
            data=json.dumps({'status': 'PREPARING'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'PREPARING')
        print("✓ Order status: PREPARING")
        
        # Update status to READY
        response = self.client.post(
            f'/api/orders/{order.id}/update_status/',
            data=json.dumps({'status': 'READY'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'READY')
        print("✓ Order status: READY")
        
        # Complete order
        response = self.client.post(f'/api/orders/{order.id}/complete/')
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'COMPLETED')
        self.assertEqual(order.completed_by, self.staff_user)
        self.assertIsNotNone(order.completed_at)
        print("✓ Order completed")
        
        # Verify cannot complete again
        response = self.client.post(f'/api/orders/{order.id}/complete/')
        self.assertEqual(response.status_code, 400)
        print("✓ Cannot complete order twice")
        
        # Verify removed from active orders
        response = self.client.get(
            f'/api/orders/active/',
            {'restaurant': str(self.restaurant.id)}
        )
        orders_data = response.json()
        order_ids = [o['id'] for o in orders_data]
        self.assertNotIn(str(order.id), order_ids)
        print("✓ Order removed from active list")
    
    def test_7_order_number_generation(self):
        """Test 7: Order number generation (A23 format)."""
        print("\n=== TEST 7: Order Number Generation ===")
        
        # Create multiple orders
        orders = []
        for i in range(5):
            order_data = {
                'customer_name': f'Customer {i}',
                'payment_method': 'CASH',
                'privacy_accepted': True,
                'items': [{'menu_item_id': str(self.menu_item1.id), 'quantity': 1}],
            }
            response = self.client.post(
                f'/api/public/r/{self.restaurant.slug}/order/',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            order_id = response.json()['order']['id']
            orders.append(Order.objects.get(id=order_id))
        
        # Verify order numbers are unique and sequential
        order_numbers = [o.order_number for o in orders]
        self.assertEqual(len(order_numbers), len(set(order_numbers)))
        
        # Verify format (A1, A2, A3, etc.)
        for order in orders:
            self.assertRegex(order.order_number, r'^[A-Z]\d+$')
            print(f"  Order {order.daily_sequence}: {order.order_number}")
        
        print("✓ All order numbers unique and correctly formatted")
    
    def test_8_database_integrity(self):
        """Test 8: Database integrity check."""
        print("\n=== TEST 8: Database Integrity ===")
        
        # Create order
        order = self.test_1_customer_order_flow_cash()
        
        # Verify no orphan records
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 2)
        for item in order_items:
            self.assertIsNotNone(item.menu_item)
            self.assertIsNotNone(item.order)
        
        # Verify audit logs
        audit_logs = AuditLog.objects.filter(entity_id=str(order.id))
        self.assertGreater(audit_logs.count(), 0)
        print(f"✓ {audit_logs.count()} audit log entries for order")
        
        # Verify no duplicate order numbers for same day
        today_orders = Order.objects.filter(
            restaurant=self.restaurant,
            created_at__date=order.created_at.date()
        )
        order_numbers = [o.order_number for o in today_orders]
        self.assertEqual(len(order_numbers), len(set(order_numbers)))
        print("✓ No duplicate order numbers")
    
    def test_9_cross_restaurant_isolation(self):
        """Test 9: Cross-restaurant isolation."""
        print("\n=== TEST 9: Cross-Restaurant Isolation ===")
        
        # Create another restaurant
        owner2 = User.objects.create_user(
            email='owner2@test.com',
            password='test123',
            first_name='Owner2',
            last_name='User',
            role='restaurant_owner'
        )
        
        restaurant2 = Restaurant.objects.create(
            name='Restaurant 2',
            slug='restaurant-2',
            owner=owner2,
            status='ACTIVE'
        )
        
        # Create order for restaurant 1
        order = self.test_1_customer_order_flow_cash()
        
        # Login as owner of restaurant 2
        refresh = RefreshToken.for_user(owner2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Try to access order from restaurant 1 (should fail)
        response = self.client.get(f'/api/orders/{order.id}/')
        self.assertIn(response.status_code, [403, 404])
        print("✓ Cross-restaurant access blocked")
    
    def test_10_error_handling(self):
        """Test 10: Error handling."""
        print("\n=== TEST 10: Error Handling ===")
        
        # Invalid menu item
        order_data = {
            'customer_name': 'Test',
            'payment_method': 'CASH',
            'privacy_accepted': True,
            'items': [{'menu_item_id': '00000000-0000-0000-0000-000000000000', 'quantity': 1}],
        }
        
        response = self.client.post(
            f'/api/public/r/{self.restaurant.slug}/order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn('error', error_data)
        print("✓ Invalid menu item rejected")
        
        # Invalid status transition
        order = self.test_1_customer_order_flow_cash()
        refresh = RefreshToken.for_user(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Try invalid transition (PENDING -> COMPLETED)
        response = self.client.post(
            f'/api/orders/{order.id}/update_status/',
            data=json.dumps({'status': 'COMPLETED'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        print("✓ Invalid status transition rejected")


def run_validation():
    """Run all validation tests."""
    print("=" * 60)
    print("DINEFLOW2 END-TO-END VALIDATION")
    print("=" * 60)
    
    # Create test instance
    test = E2EValidationTests()
    test.setUp()
    
    try:
        test.test_1_customer_order_flow_cash()
        test.test_2_customer_order_flow_online()
        test.test_3_staff_view_active_orders()
        test.test_4_staff_cash_permission_enforcement()
        test.test_5_staff_create_cash_order()
        test.test_6_order_completion_flow()
        test.test_7_order_number_generation()
        test.test_8_database_integrity()
        test.test_9_cross_restaurant_isolation()
        test.test_10_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_validation()
    sys.exit(0 if success else 1)
