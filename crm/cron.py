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
