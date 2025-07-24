# AutoCare Python Client

A Python client library for interacting with AutoCare Association databases and services.

## Features

- OAuth2 authentication with automatic token refresh
- Database and table listing
- Record fetching with pagination support
- Comprehensive error handling and logging
- Type safety with dataclasses
- Context manager support

## Installation

```bash
git clone <repository-url>
cd autocare-python
uv sync --all-extras
```

## Quick Start

```python
from autocare.client import AutoCareAPI

# Initialize client
with AutoCareAPI(
    client_id="your_client_id",
    client_secret="your_client_secret",
    username="your_username",
    password="your_password"
) as client:
    # List databases
    databases = client.list_databases()

    # List tables
    tables = client.list_tables("VCdb")

    # Fetch records
    records = client.fetch_all_records("VCdb", "Make")

    # Or iterate with pagination
    for record in client.fetch_records("VCdb", "BaseVehicle", limit=1000):
        print(record)
```

## API Reference

### Main Methods

- `list_databases()` - List available databases
- `list_tables(db_name)` - List tables in a database
- `fetch_records(db_name, table_name, limit=None, page_size=None)` - Fetch records with pagination
- `fetch_all_records(db_name, table_name)` - Fetch all records as a list
- `validate_credentials()` - Validate API credentials

### Data Classes

- `DatabaseInfo` - Database metadata
- `TableInfo` - Table metadata
- `APIResponse` - API response wrapper

### Exceptions

- `AuthenticationError` - Authentication failures
- `APIConnectionError` - Connection issues
- `APIResponseError` - API error responses
- `DataValidationError` - Data validation failures

## Development

### Setup

```bash
# Install dev dependencies
just dev-sync

# Install pre-commit hooks
just install-hooks
```

### Commands

```bash
just validate    # Run all checks (format, lint, test)
just format      # Format code
just lint        # Run linting
just test        # Run tests
```

## Configuration

Set environment variables or use parameters:

```bash
AUTOCARE_CLIENT_ID=your_client_id
AUTOCARE_CLIENT_SECRET=your_client_secret
AUTOCARE_USERNAME=your_username
AUTOCARE_PASSWORD=your_password
```

## Requirements

- Python 3.13+
- Valid AutoCare API credentials

## License

MIT License
