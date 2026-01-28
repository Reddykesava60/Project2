"""
Comprehensive Manual Testing Script for DineFlow2
Tests all user flows and verifies database integrity.

⚠️ DO NOT modify payment-related code.
This script only tests and verifies - it does not change payment logic.
"""

import os
import sys
import django
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client, override_settings, TestCase
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone
from django.conf import settings

from apps.restaurants.models import Restaurant, Staff
from apps.menu.models import MenuCategory, MenuItem
from apps.orders.models import Order, OrderItem, DailyOrderSequence
from apps.core.audit import AuditLog

User = get_user_model()


class DatabaseVerifier:
    """Verify database integrity directly via SQLite."""
    
    def __init__(self, db_path='db.sqlite3'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def query(self, sql, params=None):
        """Execute SQL query and return results."""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()
    
    def verify_orders(self):
        """Verify orders table integrity."""
        print("\n" + "="*60)
        print("DATABASE VERIFICATION: Orders Table")
        print("="*60)
        
        orders = self.query("SELECT * FROM orders_order ORDER BY created_at DESC LIMIT 10")
        print(f"\nTotal orders in database: {len(orders)}")
        
        for order in orders:
            print(f"\nOrder ID: {order['id']}")
            print(f"  Order Number: {order['order_number']}")
            print(f"  Restaurant ID: {order['restaurant_id']}")
            print(f"  Status: {order['status']}")
            print(f"  Payment Method: {order['payment_method']}")
            print(f"  Payment Status: {order['payment_status']}")
            print(f"  Total Amount: {order['total_amount']}")
            print(f"  Created At: {order['created_at']}")
        
        # Check for duplicates
        duplicates = self.query("""
            SELECT order_number, COUNT(*) as count 
            FROM orders_order 
            WHERE DATE(created_at) = DATE('now')
            GROUP BY order_number 
            HAVING count > 1
        """)
        
        if duplicates:
            print(f"\n[WARNING] Found {len(duplicates)} duplicate order numbers today!")
            for dup in duplicates:
                print(f"  Order Number: {dup['order_number']}, Count: {dup['count']}")
        else:
            print("\n[OK] No duplicate order numbers found")
        
        # Check for orphan orders (no restaurant)
        orphans = self.query("""
            SELECT o.id, o.order_number 
            FROM orders_order o 
            LEFT JOIN restaurants_restaurant r ON o.restaurant_id = r.id 
            WHERE r.id IS NULL
        """)
        
        if orphans:
            print(f"\n[WARNING] Found {len(orphans)} orphan orders!")
            for orphan in orphans:
                print(f"  Order ID: {orphan['id']}, Order Number: {orphan['order_number']}")
        else:
            print("\n[OK] No orphan orders found")
    
    def verify_order_items(self):
        """Verify order items table integrity."""
        print("\n" + "="*60)
        print("DATABASE VERIFICATION: OrderItems Table")
        print("="*60)
        
        items = self.query("""
            SELECT oi.*, o.order_number, o.restaurant_id
            FROM orders_orderitem oi
            JOIN orders_order o ON oi.order_id = o.id
            ORDER BY o.created_at DESC
            LIMIT 20
        """)
        
        print(f"\nTotal order items in database: {len(items)}")
        
        # Check for orphan items (no order)
        orphans = self.query("""
            SELECT oi.id, oi.menu_item_name
            FROM orders_orderitem oi
            LEFT JOIN orders_order o ON oi.order_id = o.id
            WHERE o.id IS NULL
        """)
        
        if orphans:
            print(f"\n[WARNING] Found {len(orphans)} orphan order items!")
            for orphan in orphans:
                print(f"  Item ID: {orphan['id']}, Name: {orphan['menu_item_name']}")
        else:
            print("\n[OK] No orphan order items found")
        
        # Check for items with invalid menu_item_id
        invalid_items = self.query("""
            SELECT oi.id, oi.menu_item_name, oi.menu_item_id
            FROM orders_orderitem oi
            LEFT JOIN menu_menuitem m ON oi.menu_item_id = m.id
            WHERE oi.menu_item_id IS NOT NULL AND m.id IS NULL
        """)
        
        if invalid_items:
            print(f"\n[WARNING] Found {len(invalid_items)} items with invalid menu_item_id!")
            for item in invalid_items:
                print(f"  Item ID: {item['id']}, Menu Item ID: {item['menu_item_id']}")
        else:
            print("\n[OK] All order items have valid menu_item_id references")
    
    def verify_audit_logs(self):
        """Verify audit logs table integrity."""
        print("\n" + "="*60)
        print("DATABASE VERIFICATION: AuditLogs Table")
        print("="*60)
        
        logs = self.query("""
            SELECT * FROM core_auditlog 
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        
        print(f"\nTotal audit logs in database: {len(logs)}")
        
        recent_logs = self.query("""
            SELECT action, COUNT(*) as count
            FROM core_auditlog
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY action
            ORDER BY count DESC
        """)
        
        print("\nRecent audit log actions (last 24 hours):")
        for log in recent_logs:
            print(f"  {log['action']}: {log['count']} occurrences")
        
        # Check for orphan logs (no user)
        orphans = self.query("""
            SELECT al.id, al.action, al.user_id
            FROM core_auditlog al
            LEFT JOIN users_user u ON al.user_id = u.id
            WHERE al.user_id IS NOT NULL AND u.id IS NULL
        """)
        
        if orphans:
            print(f"\n[WARNING] Found {len(orphans)} orphan audit logs!")
        else:
            print("\n[OK] No orphan audit logs found")
    
    def verify_payments(self):
        """Verify payment-related data."""
        print("\n" + "="*60)
        print("DATABASE VERIFICATION: Payment Data")
        print("="*60)
        
        # Check payment status distribution
        payment_statuses = self.query("""
            SELECT payment_status, COUNT(*) as count
            FROM orders_order
            GROUP BY payment_status
        """)
        
        print("\nPayment Status Distribution:")
        for status in payment_statuses:
            print(f"  {status['payment_status']}: {status['count']} orders")
        
        # Check payment method distribution
        payment_methods = self.query("""
            SELECT payment_method, COUNT(*) as count
            FROM orders_order
            GROUP BY payment_method
        """)
        
        print("\nPayment Method Distribution:")
        for method in payment_methods:
            print(f"  {method['payment_method']}: {method['count']} orders")
        
        # Check for orders with payment_id but no payment_status
        invalid_payments = self.query("""
            SELECT id, order_number, payment_id, payment_status
            FROM orders_order
            WHERE payment_id IS NOT NULL AND payment_status = 'PENDING'
        """)
        
        if invalid_payments:
            print(f"\n[WARNING] Found {len(invalid_payments)} orders with payment_id but status PENDING!")
            for order in invalid_payments:
                print(f"  Order: {order['order_number']}, Payment ID: {order['payment_id']}")
        else:
            print("\n[OK] All orders with payment_id have appropriate payment_status")
    
    def verify_revenue_totals(self):
        """Verify revenue calculations match database."""
        print("\n" + "="*60)
        print("DATABASE VERIFICATION: Revenue Totals")
        print("="*60)
        
        # Total revenue
        total_revenue = self.query("""
            SELECT SUM(total_amount) as total
            FROM orders_order
            WHERE payment_status = 'SUCCESS' AND status = 'COMPLETED'
        """)[0]
        
        print(f"\nTotal Completed Revenue: {total_revenue['total'] or 0}")
        
        # Cash revenue
        cash_revenue = self.query("""
            SELECT SUM(total_amount) as total
            FROM orders_order
            WHERE payment_method = 'CASH' 
            AND payment_status = 'SUCCESS' 
            AND status = 'COMPLETED'
        """)[0]
        
        print(f"Cash Revenue: {cash_revenue['total'] or 0}")
        
        # Online revenue
        online_revenue = self.query("""
            SELECT SUM(total_amount) as total
            FROM orders_order
            WHERE payment_method = 'ONLINE' 
            AND payment_status = 'SUCCESS' 
            AND status = 'COMPLETED'
        """)[0]
        
        print(f"Online Revenue: {online_revenue['total'] or 0}")
        
        # Today's revenue
        today_revenue = self.query("""
            SELECT SUM(total_amount) as total
            FROM orders_order
            WHERE DATE(created_at) = DATE('now')
            AND payment_status = 'SUCCESS'
        """)[0]
        
        print(f"Today's Revenue: {today_revenue['total'] or 0}")
        
        # Verify totals match
        calculated_total = (cash_revenue['total'] or 0) + (online_revenue['total'] or 0)
        if abs(calculated_total - (total_revenue['total'] or 0)) < 0.01:
            print("\n[OK] Revenue totals match correctly")
        else:
            print(f"\n[WARNING] Revenue totals don't match!")
            print(f"  Calculated: {calculated_total}, Stored: {total_revenue['total']}")
    
    def close(self):
        """Close database connection."""
        self.conn.close()


class ManualTester:
    """Manual testing helper class."""
    
    def __init__(self):
        # Use override_settings to allow testserver
        self.client = Client()
        self.db_verifier = DatabaseVerifier()
        self.test_results = []
    
    def log_test(self, test_name, status, details=""):
        """Log test result."""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[SKIP]"
        print(f"\n{status_icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def test_1_customer_order_flow_cash(self):
        """Test 1: Customer Order Flow (Cash Payment)"""
        print("\n" + "="*60)
        print("TEST 1: Customer Order Flow (Cash Payment)")
        print("="*60)
        
        try:
            # Get a restaurant
            restaurant = Restaurant.objects.filter(status='ACTIVE').first()
            if not restaurant:
                self.log_test("Customer Order Flow (Cash)", "SKIP", "No active restaurant found")
                return
            
            # Get menu items
            menu_items = MenuItem.objects.filter(
                restaurant=restaurant,
                is_available=True
            )[:2]
            
            if not menu_items.exists():
                self.log_test("Customer Order Flow (Cash)", "SKIP", "No menu items found")
                return
            
            # Create order via public endpoint
            import json
            order_data = {
                'items': [
                    {
                        'menu_item_id': str(item.id),
                        'quantity': 1
                    }
                    for item in menu_items
                ],
                'payment_method': 'CASH',
                'customer_name': 'Test Customer',
                'privacy_accepted': True
            }
            
            response = self.client.post(
                f'/api/public/r/{restaurant.slug}/order/',
                data=json.dumps(order_data),
                content_type='application/json',
                HTTP_HOST='testserver'
            )
            
            if response.status_code == 201:
                order_data = response.json()
                order_id = order_data.get('order', {}).get('id') or order_data.get('id')
                
                # Verify in database
                order = Order.objects.get(id=order_id)
                
                # Verify order items
                items_count = order.items.count()
                
                self.log_test(
                    "Customer Order Flow (Cash)",
                    "PASS",
                    f"Order {order.order_number} created with {items_count} items"
                )
                
                # Verify database state
                self.db_verifier.verify_orders()
                
            else:
                self.log_test(
                    "Customer Order Flow (Cash)",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.content.decode()}"
                )
        
        except Exception as e:
            self.log_test("Customer Order Flow (Cash)", "FAIL", str(e))
    
    def test_2_customer_order_flow_online(self):
        """Test 2: Customer Order Flow (Online Payment)"""
        print("\n" + "="*60)
        print("TEST 2: Customer Order Flow (Online Payment)")
        print("="*60)
        
        try:
            restaurant = Restaurant.objects.filter(status='ACTIVE').first()
            if not restaurant:
                self.log_test("Customer Order Flow (Online)", "SKIP", "No active restaurant found")
                return
            
            menu_items = MenuItem.objects.filter(
                restaurant=restaurant,
                is_available=True
            )[:2]
            
            if not menu_items.exists():
                self.log_test("Customer Order Flow (Online)", "SKIP", "No menu items found")
                return
            
            # Create order via public endpoint
            import json
            order_data = {
                'items': [
                    {
                        'menu_item_id': str(item.id),
                        'quantity': 1
                    }
                    for item in menu_items
                ],
                'payment_method': 'ONLINE',
                'customer_name': 'Test Customer Online',
                'privacy_accepted': True
            }
            
            response = self.client.post(
                f'/api/public/r/{restaurant.slug}/order/',
                data=json.dumps(order_data),
                content_type='application/json',
                HTTP_HOST='testserver'
            )
            
            if response.status_code == 201:
                order_data = response.json()
                order_id = order_data.get('order', {}).get('id') or order_data.get('id')
                
                # Verify in database
                order = Order.objects.get(id=order_id)
                
                # Verify payment status is PENDING
                if order.payment_status == 'PENDING' and order.payment_method == 'ONLINE':
                    self.log_test(
                        "Customer Order Flow (Online)",
                        "PASS",
                        f"Order {order.order_number} created with PENDING payment status"
                    )
                else:
                    self.log_test(
                        "Customer Order Flow (Online)",
                        "FAIL",
                        f"Payment status: {order.payment_status}, Method: {order.payment_method}"
                    )
            else:
                self.log_test(
                    "Customer Order Flow (Online)",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.content.decode()}"
                )
        
        except Exception as e:
            self.log_test("Customer Order Flow (Online)", "FAIL", str(e))
    
    def test_3_staff_active_orders(self):
        """Test 3: Staff Active Orders View"""
        print("\n" + "="*60)
        print("TEST 3: Staff Active Orders View")
        print("="*60)
        
        try:
            # Get a staff user
            staff = User.objects.filter(role='staff', restaurant__isnull=False).first()
            if not staff:
                self.log_test("Staff Active Orders", "SKIP", "No staff user found")
                return
            
            # Login
            self.client.force_login(staff)
            
            # Get active orders
            response = self.client.get('/api/orders/active/', HTTP_HOST='testserver')
            
            if response.status_code == 200:
                orders = response.json()
                active_count = len(orders) if isinstance(orders, list) else 0
                
                self.log_test(
                    "Staff Active Orders",
                    "PASS",
                    f"Retrieved {active_count} active orders"
                )
            else:
                self.log_test(
                    "Staff Active Orders",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.content.decode()}"
                )
        
        except Exception as e:
            self.log_test("Staff Active Orders", "FAIL", str(e))
    
    def test_4_order_completion(self):
        """Test 4: Order Completion"""
        print("\n" + "="*60)
        print("TEST 4: Order Completion")
        print("="*60)
        
        try:
            # Get a staff user
            staff = User.objects.filter(role='staff', restaurant__isnull=False).first()
            if not staff:
                self.log_test("Order Completion", "SKIP", "No staff user found")
                return
            
            # Get an order that can be completed
            order = Order.objects.filter(
                restaurant=staff.restaurant,
                status__in=['PENDING', 'PREPARING', 'READY'],
                payment_status='SUCCESS'
            ).first()
            
            if not order:
                self.log_test("Order Completion", "SKIP", "No completable order found")
                return
            
            self.client.force_login(staff)
            
            # Complete order
            response = self.client.post(f'/api/orders/{order.id}/complete/', HTTP_HOST='testserver')
            
            if response.status_code == 200:
                order.refresh_from_db()
                if order.status == 'COMPLETED':
                    self.log_test(
                        "Order Completion",
                        "PASS",
                        f"Order {order.order_number} completed successfully"
                    )
                else:
                    self.log_test(
                        "Order Completion",
                        "FAIL",
                        f"Order status is {order.status}, expected COMPLETED"
                    )
            else:
                self.log_test(
                    "Order Completion",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.content.decode()}"
                )
        
        except Exception as e:
            self.log_test("Order Completion", "FAIL", str(e))
    
    def test_5_database_integrity(self):
        """Test 5: Database Integrity Check"""
        print("\n" + "="*60)
        print("TEST 5: Database Integrity Check")
        print("="*60)
        
        try:
            self.db_verifier.verify_orders()
            self.db_verifier.verify_order_items()
            self.db_verifier.verify_audit_logs()
            self.db_verifier.verify_payments()
            self.db_verifier.verify_revenue_totals()
            
            self.log_test("Database Integrity", "PASS", "All integrity checks completed")
        
        except Exception as e:
            self.log_test("Database Integrity", "FAIL", str(e))
    
    @override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def run_all_tests(self):
        """Run all manual tests."""
        print("\n" + "="*60)
        print("COMPREHENSIVE MANUAL TESTING - DineFlow2")
        print("="*60)
        print(f"Started at: {datetime.now().isoformat()}")
        
        # Run tests
        self.test_1_customer_order_flow_cash()
        self.test_2_customer_order_flow_online()
        self.test_3_staff_active_orders()
        self.test_4_order_completion()
        self.test_5_database_integrity()
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.test_results if r['status'] == 'SKIP')
        
        print(f"\nTotal Tests: {len(self.test_results)}")
        print(f"[PASS] Passed: {passed}")
        print(f"[FAIL] Failed: {failed}")
        print(f"[SKIP] Skipped: {skipped}")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "[PASS]" if result['status'] == "PASS" else "[FAIL]" if result['status'] == "FAIL" else "[SKIP]"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result['details']:
                print(f"   {result['details']}")
        
        self.db_verifier.close()
        
        return {
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': len(self.test_results)
        }


if __name__ == '__main__':
    # Use override_settings for test client
    from django.test.utils import override_settings
    
    # Temporarily modify ALLOWED_HOSTS for testing
    original_allowed_hosts = list(settings.ALLOWED_HOSTS)
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1', '*']
    
    try:
        tester = ManualTester()
        results = tester.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if results['failed'] == 0 else 1)
    finally:
        # Restore original ALLOWED_HOSTS
        settings.ALLOWED_HOSTS = original_allowed_hosts
