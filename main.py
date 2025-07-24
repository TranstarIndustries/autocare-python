import os
from autocare.client import AutoCareAPI

if __name__ == "__main__":
    client_id = os.getenv("AUTOCARE_CLIENT_ID")
    client_secret = os.getenv("AUTOCARE_CLIENT_SECRET")
    username = os.getenv("AUTOCARE_USERNAME")
    password = os.getenv("AUTOCARE_PASSWORD")

    if all([client_id, client_secret, username, password]):
        try:
            with AutoCareAPI(client_id, client_secret, username, password) as api:
                # List available databases
                databases = api.list_databases()
                print(f"Available databases: {[db.name for db in databases]}")

                # Example: List tables in first database
                if databases:
                    tables = api.list_tables(databases[0].name)
                    print(f"Tables in {databases[0].name}: {[t.name for t in tables]}")

        except Exception as e:
            print(f"Error: {e}")
    else:
        print(
            "Please set environment variables: AUTOCARE_CLIENT_ID, AUTOCARE_CLIENT_SECRET, AUTOCARE_USERNAME, AUTOCARE_PASSWORD"
        )
