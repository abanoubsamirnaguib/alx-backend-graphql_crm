#!/usr/bin/env python
"""
Script to send order reminders for orders created within the last 7 days.
Uses GraphQL to query the orders and logs reminder details.
"""

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta
import os

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"

# GraphQL query to fetch orders from the last 7 days
ORDERS_QUERY = gql("""
    query {
        allOrders(orderDateGte: "%s") {
            edges {
                node {
                    id
                    customer {
                        email
                    }
                    orderDate
                }
            }
        }
    }
""")

def get_orders_from_last_7_days():
    """Fetch orders created within the last 7 days from GraphQL endpoint."""
    try:
        # Calculate date 7 days ago
        date_7_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        # Format the query with the date
        query = gql(f"""
            query {{
                allOrders(orderDateGte: "{date_7_days_ago}") {{
                    edges {{
                        node {{
                            id
                            customer {{
                                email
                            }}
                            orderDate
                        }}
                    }}
                }}
            }}
        """)
        
        # Create transport and client
        transport = RequestsHTTPTransport(url=GRAPHQL_URL)
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # Execute query
        result = client.execute(query)
        return result
    except Exception as e:
        print(f"Error fetching orders from GraphQL: {e}")
        return None

def log_order_reminders(orders_result):
    """Log order reminders with timestamp to the log file."""
    if not orders_result:
        print("No orders found or error occurred.")
        return
    
    try:
        with open(LOG_FILE, "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract orders from GraphQL response
            edges = orders_result.get("allOrders", {}).get("edges", [])
            
            if not edges:
                log.write(f"[{timestamp}] No orders found for reminders.\n")
                return
            
            # Log each order
            for edge in edges:
                node = edge.get("node", {})
                order_id = node.get("id", "Unknown")
                customer_email = node.get("customer", {}).get("email", "Unknown")
                
                log_entry = f"[{timestamp}] Order ID: {order_id}, Customer Email: {customer_email}\n"
                log.write(log_entry)
        
        print(f"Logged {len(edges)} order reminders.")
    except Exception as e:
        print(f"Error logging order reminders: {e}")

def main():
    """Main function to process order reminders."""
    # Fetch orders from last 7 days
    orders_result = get_orders_from_last_7_days()
    
    # Log the reminders
    log_order_reminders(orders_result)
    
    # Print completion message
    print("Order reminders processed!")

if __name__ == "__main__":
    main()
