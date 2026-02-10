"""
Integration tests for AutoCare API Client.

These tests hit real API endpoints and require valid credentials
in environment variables. Skipped by default in CI.

Run manually with: uv run pytest tests/test_integration.py -m integration -v
"""

import os

import pytest

from autocare.client import AutoCareAPI
from autocare.databases.vcdb import Vehicle, Make
from autocare.databases.pcdb import Part
from autocare.databases.padb import PartAttribute
from autocare.databases.qdb import Qualifier
from autocare.databases.brand import Brand
from autocare.compatibility.field_mapping import migrate_vcdb_record


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


@pytest.mark.integration
@skip_no_creds
class TestIntegrationTypedModels:
    """Test typed model fetching against real API."""

    def test_fetch_vcdb_vehicle_typed(self, api_client):
        """Test fetching VCdb Vehicle as typed model."""
        records = list(
            api_client.fetch_records("vcdb", "Vehicle", limit=2, model=Vehicle)
        )
        assert len(records) == 2
        assert isinstance(records[0], Vehicle)
        assert records[0].VehicleID is not None
        assert records[0].BaseVehicleID is not None
        assert records[0].EffectiveDateTime is not None

    def test_fetch_vcdb_make_typed(self, api_client):
        """Test fetching VCdb Make as typed model with CultureID."""
        records = list(api_client.fetch_records("vcdb", "Make", limit=1, model=Make))
        assert len(records) == 1
        assert isinstance(records[0], Make)
        assert records[0].MakeName is not None
        assert records[0].CultureID is not None

    def test_fetch_pcdb_part_typed(self, api_client):
        """Test fetching PCdb Part as typed model."""
        records = list(api_client.fetch_records("pcdb", "Parts", limit=1, model=Part))
        assert len(records) == 1
        assert isinstance(records[0], Part)
        assert records[0].PartTerminologyID is not None
        assert records[0].PartTerminologyName is not None

    def test_fetch_padb_attribute_typed(self, api_client):
        """Test fetching PAdb PartAttribute as typed model."""
        records = list(
            api_client.fetch_records(
                "padb", "PartAttributes", limit=1, model=PartAttribute
            )
        )
        assert len(records) == 1
        assert isinstance(records[0], PartAttribute)
        assert records[0].PAID is not None

    def test_fetch_qdb_qualifier_typed(self, api_client):
        """Test fetching Qdb Qualifier as typed model."""
        records = list(
            api_client.fetch_records("qdb", "Qualifier", limit=1, model=Qualifier)
        )
        assert len(records) == 1
        assert isinstance(records[0], Qualifier)
        assert records[0].QualifierID is not None

    def test_fetch_brand_typed(self, api_client):
        """Test fetching Brand as typed model."""
        records = list(
            api_client.fetch_records("brand", "BrandTable", limit=1, model=Brand)
        )
        assert len(records) == 1
        assert isinstance(records[0], Brand)
        assert records[0].BrandID is not None

    def test_fetch_all_records_typed(self, api_client):
        """Test fetch_all_records with model param."""
        records = api_client.fetch_all_records("qdb", "Qualifier", model=Qualifier)
        assert len(records) > 0
        assert all(isinstance(r, Qualifier) for r in records)


@pytest.mark.integration
@skip_no_creds
class TestIntegrationFieldMapping:
    """Test field mapping against real API records."""

    def test_migrate_vcdb_v20_to_v10(self, api_client):
        """Test stripping versioning fields from real VCdb v2.0 records."""
        records = list(api_client.fetch_records("vcdb", "Vehicle", limit=2))
        assert len(records) > 0

        for record in records:
            # Confirm v2.0 record has versioning fields
            assert "EffectiveDateTime" in record

            migrated = migrate_vcdb_record(record, "2.0", "1.0")
            assert "EffectiveDateTime" not in migrated
            assert "EndDateTime" not in migrated
            assert "CultureID" not in migrated
            assert migrated["VehicleID"] == record["VehicleID"]

    def test_migrate_vcdb_roundtrip(self, api_client):
        """Test that migrating v2.0 -> v1.0 -> v2.0 preserves core fields."""
        records = list(api_client.fetch_records("vcdb", "Vehicle", limit=1))
        original = records[0]

        v1 = migrate_vcdb_record(original, "2.0", "1.0")
        v2 = migrate_vcdb_record(v1, "1.0", "2.0")

        # Core data fields should survive the roundtrip
        assert v2["VehicleID"] == original["VehicleID"]
        assert v2["BaseVehicleID"] == original["BaseVehicleID"]
        # Versioning fields are lost in the downgrade (expected)
        assert v2["EffectiveDateTime"] is None
