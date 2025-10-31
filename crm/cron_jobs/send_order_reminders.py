#!/usr/bin/env python
"""
Script to send order reminders for orders created within the last 7 days.
Uses GraphQL to query the orders and logs reminder details.
"""

import django
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

import graphene
from crm.schema import Query as CRMQuery
from crm.models import Order

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"

def get_orders_from_last_7_days():
    """Fetch orders created within the last 7 days using Django ORM."""
    try:
        # Calculate date 7 days ago
        date_7_days_ago = datetime.now() - timedelta(days=7)
        
        # Query orders using Django ORM
        orders = Order.objects.filter(order_date__gte=date_7_days_ago).select_related('customer')
        
        return orders
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return None

def log_order_reminders(orders):
    """Log order reminders with timestamp to the log file."""
    if not orders:
        print("No orders found or error occurred.")
        return
    
    try:
        with open(LOG_FILE, "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            order_count = orders.count()
            
            if order_count == 0:
                log.write(f"[{timestamp}] No orders found for reminders.\n")
                return
            
            # Log each order
            for order in orders:
                order_id = order.id
                customer_email = order.customer.email
                customer_name = order.customer.name
                
                log_entry = f"[{timestamp}] Order ID: {order_id}, Customer: {customer_name} ({customer_email})\n"
                log.write(log_entry)
        
        print(f"Logged {order_count} order reminders.")
    except Exception as e:
        print(f"Error logging order reminders: {e}")

def main():
    """Main function to process order reminders."""
    # Fetch orders from last 7 days
    orders = get_orders_from_last_7_days()
    
    # Log the reminders
    log_order_reminders(orders)
    
    # Print completion message
    print("Order reminders processed!")

if __name__ == "__main__":
    main()
