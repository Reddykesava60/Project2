"""
Analytics views for restaurant owners.
Provides business insights and reporting.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncHour, TruncDate
from datetime import timedelta
from decimal import Decimal

from apps.core.permissions import IsOwner
from apps.restaurants.models import Restaurant
from .models import Order


class DailyAnalyticsView(APIView):
    """
    Get daily analytics for a restaurant.
    
    Query params:
    - restaurant: Restaurant ID (required for owners with multiple restaurants)
    - date: Date in YYYY-MM-DD format (default: today)
    - days: Number of days to include (default: 7)
    """
    
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get(self, request):
        user = request.user
        restaurant_id = request.query_params.get('restaurant')
        
        # Get restaurant
        try:
            if restaurant_id:
                restaurant = Restaurant.objects.get(id=restaurant_id, owner=user)
            else:
                # Default to first owned restaurant
                restaurant = user.owned_restaurants.first()
                if not restaurant:
                    return Response(
                        {
                            'error': 'NO_RESTAURANT',
                            'message': 'No restaurant found for this user.'
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
        except Restaurant.DoesNotExist:
            return Response(
                {
                    'error': 'RESTAURANT_NOT_FOUND',
                    'message': 'Restaurant not found or access denied.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parse date parameters
        try:
            days = int(request.query_params.get('days', 7))
            days = min(days, 90)  # Max 90 days
        except ValueError:
            days = 7
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        # Get orders for date range (tenant-scoped)
        orders = Order.objects.filter(
            restaurant=restaurant,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Daily breakdown - revenue only from completed orders with successful payment (lowercase)
        daily_stats = orders.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            order_count=Count('id'),
            revenue=Sum('total_amount', filter=Q(status='completed', payment_status='success')),
            avg_order_value=Avg('total_amount', filter=Q(status='completed', payment_status='success')),
            completed=Count('id', filter=Q(status='completed', payment_status='success')),
            # Note: 'cancelled' status no longer exists per PRD - count as 0
            cancelled=Count('id', filter=Q(status='cancelled')),  # Will always be 0
        ).order_by('date')
        
        # Hourly breakdown for today - revenue only from completed orders with successful payment
        today_orders = orders.filter(created_at__date=end_date)
        hourly_stats = today_orders.annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            order_count=Count('id'),
            revenue=Sum('total_amount', filter=Q(status='completed', payment_status='success')),
        ).order_by('hour')
        
        # Summary stats - only count completed orders with successful payment (lowercase)
        total_orders = orders.count()
        completed_orders = orders.filter(
            status='completed',
            payment_status='success'
        ).count()
        total_revenue = orders.filter(
            status='completed',
            payment_status='success'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        avg_order_value = total_revenue / completed_orders if completed_orders > 0 else Decimal('0')
        
        # Cash vs UPI breakdown - only completed orders with successful payment (lowercase)
        payment_breakdown = orders.filter(
            status='completed',
            payment_status='success'
        ).values('payment_method').annotate(
            count=Count('id'),
            revenue=Sum('total_amount')
        )
        
        # Top selling items - only from completed orders with successful payment (lowercase)
        from .models import OrderItem
        top_items = OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__created_at__date__gte=start_date,
            order__status='completed',
            order__payment_status='success'
        ).values('menu_item_name').annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('subtotal')
        ).order_by('-quantity_sold')[:10]
        
        # Peak hours - only completed orders with successful payment (lowercase)
        peak_hours = orders.filter(
            status='completed',
            payment_status='success'
        ).values('hour_of_day').annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:5]
        
        return Response({
            'restaurant': {
                'id': str(restaurant.id),
                'name': restaurant.name,
                'currency': restaurant.currency,
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days,
            },
            'summary': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'completed_orders': completed_orders,
                'average_order_value': float(avg_order_value),
                'completion_rate': round(completed_orders / total_orders * 100, 1) if total_orders > 0 else 0,
            },
            'daily_breakdown': [
                {
                    'date': stat['date'].isoformat() if stat['date'] else None,
                    'orders': stat['order_count'],
                    'revenue': float(stat['revenue'] or 0),
                    'avg_order_value': float(stat['avg_order_value'] or 0),
                }
                for stat in daily_stats
            ],
            'hourly_breakdown': [
                {
                    'hour': stat['hour'].strftime('%H:00') if stat['hour'] else None,
                    'orders': stat['order_count'],
                    'revenue': float(stat['revenue'] or 0),
                }
                for stat in hourly_stats
            ],
            'payment_breakdown': [
                {
                    'method': item['payment_method'],
                    'count': item['count'],
                    'revenue': float(item['revenue'] or 0),
                }
                for item in payment_breakdown
            ],
            'top_items': [
                {
                    'name': item['menu_item_name'],
                    'quantity_sold': item['quantity_sold'],
                    'revenue': float(item['revenue'] or 0),
                }
                for item in top_items
            ],
            'peak_hours': [
                {
                    'hour': f"{item['hour_of_day']:02d}:00",
                    'orders': item['order_count'],
                }
                for item in peak_hours
            ],
        })
