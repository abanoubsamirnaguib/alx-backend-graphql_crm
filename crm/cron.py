"""
Cron jobs for CRM application.
"""

from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    """
    Log a heartbeat message every 5 minutes to confirm the CRM application's health.
    Logs to /tmp/crm_heartbeat_log.txt in the format: DD/MM/YYYY-HH:MM:SS CRM is alive
    Optionally queries the GraphQL hello field to verify the endpoint is responsive.
    """
    try:
        log_file = "/tmp/crm_heartbeat_log.txt"
        
        # Format timestamp as DD/MM/YYYY-HH:MM:SS
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        heartbeat_message = f"{timestamp} CRM is alive"
        
        # Try to query GraphQL endpoint for additional verification (optional)
        try:
            query = gql("""
                query {
                    hello
                }
            """)
            transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
            client = Client(transport=transport, fetch_schema_from_transport=False)
            result = client.execute(query)
            
            # If successful, append additional info
            if result:
                heartbeat_message += " | GraphQL endpoint responsive"
        except Exception as graphql_error:
            # Log heartbeat even if GraphQL query fails
            heartbeat_message += " | GraphQL endpoint unreachable"
        
        # Append to log file (does not overwrite)
        with open(log_file, "a") as log:
            log.write(heartbeat_message + "\n")
        
        print(f"Heartbeat logged: {heartbeat_message}")
        
    except Exception as e:
        print(f"Error logging CRM heartbeat: {e}")


def update_low_stock():
    """
    Cron job that runs every 12 hours.
    Executes the UpdateLowStockProducts GraphQL mutation.
    Logs updated product names and new stock levels to /tmp/low_stock_updates_log.txt with timestamp.
    """
    try:
        # GraphQL mutation to update low stock products
        mutation = gql("""
            mutation {
                updateLowStockProducts {
                    updatedProducts {
                        id
                        name
                        stock
                    }
                    success
                    message
                }
            }
        """)
        
        # Connect to GraphQL endpoint
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # Execute mutation
        result = client.execute(mutation)
        
        # Extract data
        update_result = result.get('updateLowStockProducts', {})
        updated_products = update_result.get('updatedProducts', [])
        success = update_result.get('success', False)
        message = update_result.get('message', '')
        
        # Format timestamp as DD/MM/YYYY-HH:MM:SS
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        
        # Prepare log content
        log_file = "/tmp/low_stock_updates_log.txt"
        log_entries = [f"\n{'='*60}"]
        log_entries.append(f"Update Time: {timestamp}")
        log_entries.append(f"Status: {'SUCCESS' if success else 'FAILED'}")
        log_entries.append(f"Message: {message}")
        log_entries.append(f"Total Products Updated: {len(updated_products)}")
        log_entries.append("="*60)
        
        # Log each updated product
        if updated_products:
            log_entries.append("Updated Products:")
            for product in updated_products:
                log_entries.append(f"  - {product['name']}: New Stock = {product['stock']}")
        else:
            log_entries.append("No products were updated")
        
        # Write to log file (append mode)
        with open(log_file, "a", encoding="utf-8") as log:
            for entry in log_entries:
                log.write(entry + "\n")
        
        print(f"Low stock update logged: {message}")
        
    except Exception as e:
        # Log the error
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        log_file = "/tmp/low_stock_updates_log.txt"
        
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"\n{timestamp} ERROR: {str(e)}\n")
        
        print(f"Error updating low stock products: {e}")
