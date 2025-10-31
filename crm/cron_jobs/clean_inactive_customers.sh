#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")/../.." || exit 1

# Get the current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Run Django shell command to delete inactive customers
# Customers with no orders since one year ago will be deleted
RESULT=$(python manage.py shell <<EOF
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer, Order

# Calculate the date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders in the last year
# Get all customers
all_customers = Customer.objects.all()
inactive_customers = []

for customer in all_customers:
    # Get the latest order for this customer
    latest_order = Order.objects.filter(customer=customer).order_by('-order_date').first()
    
    # If customer has no orders or latest order is older than one year
    if latest_order is None or latest_order.order_date < one_year_ago:
        inactive_customers.append(customer)

# Delete inactive customers and count them
deleted_count = len(inactive_customers)
for customer in inactive_customers:
    customer.delete()

print(f"Deleted {deleted_count} inactive customers")
EOF
)

# Log the result with timestamp
echo "[$TIMESTAMP] $RESULT" >> /tmp/customer_cleanup_log.txt
