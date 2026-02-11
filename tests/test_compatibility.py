"""Tests for field mapping / compatibility layer."""

import pytest

from autocare.compatibility.field_mapping import (
    migrate_aces_record,
    migrate_vcdb_record,
    migrate_padb_record,
)


class TestMigrateACESRecord:
    """Test ACES record migration between versions."""

    def test_v42_to_v50(self):
        """Test migrating an ACES 4.2 record to 5.0 format."""
        record = {
            "Part": "ABC123",
            "PartType": "Brake Pad",
            "BrandAAIAID": "BBBB",
            "Qty": 1,
            "Position": "Front",
        }
        result = migrate_aces_record(record, from_version="4.2", to_version="5.0")

        assert "PartNumber" in result
        assert result["PartNumber"] == "ABC123"
        assert "PartTerminology" in result
        assert result["PartTerminology"] == "Brake Pad"
        assert "BrandID" in result
        assert result["BrandID"] == "BBBB"
        # Unchanged fields remain
        assert result["Qty"] == 1
        assert result["Position"] == "Front"
        # Old keys should not be present
        assert "Part" not in result
        assert "PartType" not in result
        assert "BrandAAIAID" not in result

    def test_v50_to_v42(self):
        """Test migrating an ACES 5.0 record back to 4.2 format."""
        record = {
            "PartNumber": "ABC123",
            "PartTerminology": "Brake Pad",
            "BrandID": "BBBB",
            "Qty": 1,
        }
        result = migrate_aces_record(record, from_version="5.0", to_version="4.2")

        assert result["Part"] == "ABC123"
        assert result["PartType"] == "Brake Pad"
        assert result["BrandAAIAID"] == "BBBB"
        assert "PartNumber" not in result
        assert "PartTerminology" not in result
        assert "BrandID" not in result

    def test_same_version_noop(self):
        """Test that migrating to the same version returns a copy."""
        record = {"Part": "ABC123", "Qty": 1}
        result = migrate_aces_record(record, from_version="4.2", to_version="4.2")
        assert result == record
        assert result is not record  # Should be a copy

    def test_no_matching_fields(self):
        """Test migration when record has no fields to rename."""
        record = {"Qty": 1, "Position": "Front"}
        result = migrate_aces_record(record, from_version="4.2", to_version="5.0")
        assert result == {"Qty": 1, "Position": "Front"}

    def test_invalid_version(self):
        """Test that invalid versions raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported"):
            migrate_aces_record({}, from_version="3.0", to_version="5.0")


class TestMigrateVCdbRecord:
    """Test VCdb record migration between versions."""

    def test_v10_to_v20_adds_versioning_fields(self):
        """Test migrating a VCdb 1.0 record to 2.0 format."""
        record = {
            "VehicleID": 1,
            "BaseVehicleID": 1,
            "SubModelID": 1,
        }
        result = migrate_vcdb_record(record, from_version="1.0", to_version="2.0")

        # v2.0 records should have versioning fields set to None if not present
        assert result["VehicleID"] == 1
        assert result.get("EffectiveDateTime") is None
        assert result.get("EndDateTime") is None

    def test_v20_to_v10_strips_versioning_fields(self):
        """Test migrating a VCdb 2.0 record to 1.0 format."""
        record = {
            "VehicleID": 1,
            "BaseVehicleID": 1,
            "EffectiveDateTime": "2024-01-01T00:00:00Z",
            "EndDateTime": None,
            "CultureID": "en-US",
        }
        result = migrate_vcdb_record(record, from_version="2.0", to_version="1.0")

        assert result["VehicleID"] == 1
        assert "EffectiveDateTime" not in result
        assert "EndDateTime" not in result
        assert "CultureID" not in result

    def test_same_version_noop(self):
        """Test same version migration returns a copy."""
        record = {"VehicleID": 1}
        result = migrate_vcdb_record(record, from_version="2.0", to_version="2.0")
        assert result == record
        assert result is not record

    def test_invalid_version(self):
        with pytest.raises(ValueError, match="Unsupported"):
            migrate_vcdb_record({}, from_version="3.0", to_version="1.0")


class TestMigratePAdbRecord:
    """Test PAdb record migration between versions."""

    def test_v40_to_v50_adds_versioning_fields(self):
        """Test migrating a PAdb 4.0 record to 5.0 format."""
        record = {
            "PAID": 10060,
            "PAName": "12 Volt Compatible",
        }
        result = migrate_padb_record(record, from_version="4.0", to_version="5.0")

        assert result["PAID"] == 10060
        assert result.get("EffectiveDateTime") is None
        assert result.get("EndDateTime") is None

    def test_v50_to_v40_strips_versioning_fields(self):
        """Test migrating a PAdb 5.0 record to 4.0 format."""
        record = {
            "PAID": 10060,
            "PAName": "12 Volt Compatible",
            "CultureID": "en-US",
            "EffectiveDateTime": "2023-03-07T16:46:33.253",
            "EndDateTime": None,
        }
        result = migrate_padb_record(record, from_version="5.0", to_version="4.0")

        assert result["PAID"] == 10060
        assert "EffectiveDateTime" not in result
        assert "EndDateTime" not in result
        assert "CultureID" not in result

    def test_same_version_noop(self):
        record = {"PAID": 1}
        result = migrate_padb_record(record, from_version="5.0", to_version="5.0")
        assert result == record
        assert result is not record

    def test_invalid_version(self):
        with pytest.raises(ValueError, match="Unsupported"):
            migrate_padb_record({}, from_version="1.0", to_version="5.0")
