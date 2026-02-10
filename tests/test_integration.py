"""
Integration tests for AutoCare API Client.

These tests hit real API endpoints and require valid credentials
in environment variables. Skipped by default in CI.

Run manually with: uv run pytest tests/test_integration.py -m integration -v
"""

import os

import pytest

from autocare.client import AutoCareAPI


def _load_env():
    """Load credentials from .env file if environment variables not set."""
    if os.getenv("AUTOCARE_CLIENT_ID"):
        return

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value


_load_env()

HAVE_CREDENTIALS = all(
    os.getenv(k)
    for k in [
        "AUTOCARE_CLIENT_ID",
        "AUTOCARE_CLIENT_SECRET",
        "AUTOCARE_USERNAME",
        "AUTOCARE_PASSWORD",
    ]
)

skip_no_creds = pytest.mark.skipif(
    not HAVE_CREDENTIALS, reason="AutoCare API credentials not available"
)


@pytest.fixture(scope="module")
def api_client():
    """Create a shared API client for integration tests."""
    client = AutoCareAPI(
        client_id=os.environ["AUTOCARE_CLIENT_ID"],
        client_secret=os.environ["AUTOCARE_CLIENT_SECRET"],
        username=os.environ["AUTOCARE_USERNAME"],
        password=os.environ["AUTOCARE_PASSWORD"],
    )
    yield client
    client.close()


@pytest.mark.integration
@skip_no_creds
class TestIntegrationSmoke:
    """Basic smoke tests against real API endpoints."""

    def test_authentication(self, api_client):
        """Test that authentication succeeds."""
        assert api_client.token is not None
        assert api_client.token_expires_at > 0

    def test_list_databases(self, api_client):
        """Test listing available databases."""
        databases = api_client.list_databases()
        assert len(databases) > 0

        db_names = [db.name.lower() for db in databases]
        assert "vcdb" in db_names
        assert "pcdb" in db_names
        assert "padb" in db_names
        assert "qdb" in db_names
        assert "brand" in db_names

    def test_list_tables_vcdb(self, api_client):
        """Test listing tables in VCdb."""
        tables = api_client.list_tables("VCDB")
        assert len(tables) > 0

        table_names = [t.name for t in tables]
        assert "Vehicle" in table_names
        assert "BaseVehicle" in table_names

    def test_fetch_vcdb_record(self, api_client):
        """Test fetching a VCdb record (uses vcdb subdomain, v2.0)."""
        records = list(api_client.fetch_records("vcdb", "Vehicle", limit=1))
        assert len(records) == 1
        assert "VehicleID" in records[0]

    def test_fetch_pcdb_record(self, api_client):
        """Test fetching a PCdb record (uses pcdb subdomain, v1.0)."""
        records = list(api_client.fetch_records("pcdb", "Parts", limit=1))
        assert len(records) == 1

    def test_fetch_padb_record(self, api_client):
        """Test fetching a PAdb record (routes through pcdb subdomain)."""
        records = list(api_client.fetch_records("padb", "PartAttributes", limit=1))
        assert len(records) == 1

    def test_fetch_qdb_record(self, api_client):
        """Test fetching a Qdb record."""
        records = list(api_client.fetch_records("qdb", "Qualifier", limit=1))
        assert len(records) == 1

    def test_fetch_brand_record(self, api_client):
        """Test fetching a Brand record."""
        records = list(api_client.fetch_records("brand", "BrandTable", limit=1))
        assert len(records) == 1
