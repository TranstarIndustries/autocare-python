"""Tests for ACES and PIES standards modules."""

from autocare.standards import aces, pies


class TestACES:
    """Test ACES version constants."""

    def test_versions(self):
        assert aces.VERSIONS == ["4.2", "5.0"]

    def test_v4_elements(self):
        assert "Part" in aces.V4_ELEMENTS
        assert "PartType" in aces.V4_ELEMENTS
        assert "References" in aces.V4_ELEMENTS
        assert "DiagramReference" in aces.V4_ELEMENTS

    def test_v5_elements(self):
        assert "PartNumber" in aces.V5_ELEMENTS
        assert "PartTerminology" in aces.V5_ELEMENTS
        assert "DiagramAsset" in aces.V5_ELEMENTS
        assert "NonDiagramAssets" in aces.V5_ELEMENTS
        # Removed in v5
        assert "Part" not in aces.V5_ELEMENTS
        assert "PartType" not in aces.V5_ELEMENTS
        assert "References" not in aces.V5_ELEMENTS

    def test_element_renames(self):
        assert aces.V4_TO_V5_ELEMENT_RENAMES["Part"] == "PartNumber"
        assert aces.V4_TO_V5_ELEMENT_RENAMES["PartType"] == "PartTerminology"

    def test_reverse_element_renames(self):
        assert aces.V5_TO_V4_ELEMENT_RENAMES["PartNumber"] == "Part"
        assert aces.V5_TO_V4_ELEMENT_RENAMES["PartTerminology"] == "PartType"

    def test_removed_elements(self):
        assert "References" in aces.V5_REMOVED_ELEMENTS
        assert "DiagramReference" in aces.V5_REMOVED_ELEMENTS
        assert "AssetReference" in aces.V5_REMOVED_ELEMENTS

    def test_new_elements(self):
        assert "DiagramAsset" in aces.V5_NEW_ELEMENTS
        assert "NonDiagramAssets" in aces.V5_NEW_ELEMENTS

    def test_attribute_renames(self):
        assert aces.V4_TO_V5_ATTRIBUTE_RENAMES["BrandAAIAID"] == "BrandID"
        assert aces.V5_TO_V4_ATTRIBUTE_RENAMES["BrandID"] == "BrandAAIAID"

    def test_field_renames(self):
        assert aces.V4_TO_V5_FIELD_RENAMES["Part"] == "PartNumber"
        assert aces.V4_TO_V5_FIELD_RENAMES["BrandAAIAID"] == "BrandID"
        assert aces.V5_TO_V4_FIELD_RENAMES["PartNumber"] == "Part"


class TestPIES:
    """Test PIES version constants."""

    def test_versions(self):
        assert pies.VERSIONS == ["7.2", "8.0"]

    def test_shared_segments(self):
        assert pies.SEGMENTS["A01"] == "Header"
        assert pies.SEGMENTS["B01"] == "Item"
        assert pies.SEGMENTS["Z01"] == "Trailer"

    def test_v8_new_segments(self):
        assert pies.V8_NEW_SEGMENTS["I01"] == "PackagingItemsPackage"

    def test_v8_all_segments_includes_new(self):
        assert "I01" in pies.SEGMENTS_V8
        assert "A01" in pies.SEGMENTS_V8

    def test_v8_new_types(self):
        assert "WeightType" in pies.V8_NEW_TYPES
        assert "LanguageCodeType" in pies.V8_NEW_TYPES

    def test_v8_backward_compatible(self):
        """PIES 8.0 should have no removed or renamed segments."""
        assert pies.V8_REMOVED_SEGMENTS == {}
        assert pies.V8_RENAMED_SEGMENTS == {}

    def test_all_v72_segments_in_v8(self):
        """All 7.2 segments should still exist in 8.0."""
        for code in pies.SEGMENTS:
            assert code in pies.SEGMENTS_V8
