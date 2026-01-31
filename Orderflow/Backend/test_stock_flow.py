import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.orders.models import Order, OrderItem
from apps.menu.models import MenuItem, MenuCategory
from apps.restaurants.models import Restaurant
from apps.users.models import User
from apps.orders.payment_service import process_order_payment
from apps.orders.cleanup import cleanup_stale_pending_cash_orders
from django.utils import timezone
from datetime import timedelta

def cleanup():
    print("--- Cleaning up old test data ---")
    Order.objects.filter(total_amount=Decimal('99.99')).delete()
    MenuItem.objects.filter(name="Stock Test Item").delete()

def test_stock_flow():
    cleanup()
    
    print("\n--- Setting up Test Data ---")
    # Get or create a restaurant
    user = User.objects.filter(role__in=['OWNER', 'restaurant_owner']).first()
    if not user:
        print("SKIP: No owner user found")
        return

    restaurant = Restaurant.objects.filter(owner=user).first()
    if not restaurant:
        print("SKIP: No restaurant found")
        return
        
    category, _ = MenuCategory.objects.get_or_create(
        restaurant=restaurant, 
        name="Test Category", 
        defaults={'display_order': 0, 'is_active': True}
    )
    
    # Create Item with 10 stock
    item = MenuItem.objects.create(
        restaurant=restaurant,
        category=category,
        name="Stock Test Item",
        price=Decimal('10.00'),
        stock_quantity=10,
        is_available=True,
        is_active=True
    )
    print(f"Created Item: {item.name}, Stock: {item.stock_quantity}, Reserved: {item.reserved_stock}, Available: {item.available_stock}")
    
    # --- SCENARIO 1: Order Creation (Reservation) ---
    print("\n--- TEST 1: Reserve Stock (Order Creation) ---")
    # Simulate Order Creation (reserves stock)
    item.reserve_stock(2)
    item.refresh_from_db()
    
    print(f"Stock after reserving 2: Total={item.stock_quantity}, Reserved={item.reserved_stock}, Available={item.available_stock}")
    if item.reserved_stock != 2:
        print("FAIL: Reserved stock should be 2")
    else:
        print("PASS: Reserved stock is 2")
        
    # Create the pending order manually (mimicking serializer)
    order = Order.objects.create(
        restaurant=restaurant,
        order_number="TEST001",
        daily_sequence=1,
        total_amount=Decimal('99.99'), # Sentinel
        status='pending',
        payment_status='pending',
        payment_method='upi',
        subtotal=Decimal('20.00'),
        tax=Decimal('0.00')
    )
    OrderItem.objects.create(order=order, menu_item=item, quantity=2, price_at_order=Decimal('10.00'), menu_item_name=item.name, subtotal=Decimal('20.00'))
    
    # --- SCENARIO 2: Payment Confirmation (Webhook/Service) ---
    print("\n--- TEST 2: Confirm Payment (Deduct Stock) ---")
    # Simulate payment verification
    # We call process_order_payment logic directly or mock signature verification
    # For this test, let's artificially trigger the logic we added to payment_service/webhook
    
    from django.db import transaction
    with transaction.atomic():
        item.confirm_sale(2) # This is what the view calls
    
    item.refresh_from_db()
    print(f"Stock after confirm: Total={item.stock_quantity}, Reserved={item.reserved_stock}, Available={item.available_stock}")
    
    if item.stock_quantity == 8 and item.reserved_stock == 0:
        print("PASS: Stock deducted to 8, Reserved released to 0")
    else:
        print(f"FAIL: Expected Stock 8/Reserved 0. Got {item.stock_quantity}/{item.reserved_stock}")

    # --- SCENARIO 3: Cancellation/Stale Cleanup ---
    print("\n--- TEST 3: Stale Order Cleanup (Restore Stock) ---")
    # Reset item for cleanup test
    item.stock_quantity = 10
    item.reserved_stock = 0
    item.save()
    
    # Create stale pending cash order
    item.reserve_stock(3)
    stale_order = Order.objects.create(
        restaurant=restaurant,
        order_number="TEST002",
        daily_sequence=2,
        total_amount=Decimal('99.99'),
        status='pending',
        payment_status='pending',
        payment_method='cash',
        subtotal=Decimal('30.00'),
        tax=Decimal('0.00'),
        created_at=timezone.now() - timedelta(days=2) # Old
    )
    # Hack created_at because auto_now_add makes it read-only-ish
    Order.objects.filter(id=stale_order.id).update(created_at=timezone.now() - timedelta(days=2))
    
    OrderItem.objects.create(order=stale_order, menu_item=item, quantity=3, price_at_order=Decimal('10.00'), menu_item_name=item.name, subtotal=Decimal('30.00'))
    
    item.refresh_from_db()
    print(f"Stale Order Setup: Stock={item.stock_quantity}, Reserved={item.reserved_stock}")
    
    # Run Cleanup
    deleted = cleanup_stale_pending_cash_orders()
    item.refresh_from_db()
    
    print(f"Stock after cleanup: Total={item.stock_quantity}, Reserved={item.reserved_stock}, Available={item.available_stock}")
    
    if deleted > 0 and item.reserved_stock == 0:
         print("PASS: Validated cleanup restored reserved stock")
    else:
         print(f"FAIL: Cleanup count {deleted}, Reserved {item.reserved_stock}")

    # --- SCENARIO 4: Reservation Expiry ---
    print("\n--- TEST 4: Reservation Expiry (Release Stock) ---")
    from apps.orders.models import OrderReservation
    from apps.orders.cleanup import cleanup_expired_reservations
    
    # Reset item
    item.stock_quantity = 10
    item.reserved_stock = 0
    item.save()
    
    # Create expired reservation
    item.reserve_stock(5)
    expired_res = OrderReservation.objects.create(
        restaurant=restaurant,
        items=[{'menu_item_id': str(item.id), 'quantity': 5, 'name': item.name, 'price': 10.0, 'subtotal': 50.0}],
        total_amount=Decimal('50.00'),
        expires_at=timezone.now() - timedelta(minutes=1), # Expired
        status=OrderReservation.Status.ACTIVE,
        customer_name="Expired User",
        payment_method='upi'
    )
    
    item.refresh_from_db()
    print(f"Expired Res Setup: Reserved={item.reserved_stock}")
    
    # Run Cleanup
    cleaned = cleanup_expired_reservations()
    item.refresh_from_db()
    
    print(f"Stock after res cleanup: Total={item.stock_quantity}, Reserved={item.reserved_stock}")
    
    if cleaned > 0 and item.reserved_stock == 0:
        print("PASS: Expired reservation cleanup released stock")
    else:
        print(f"FAIL: Cleanup count {cleaned}, Reserved {item.reserved_stock}")

    cleanup()

if __name__ == "__main__":
    try:
        test_stock_flow()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
