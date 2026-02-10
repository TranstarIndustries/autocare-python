"""Tests for database-specific modules and typed response models."""

from autocare.databases.base import BaseModel, VersionedModel, CulturedModel
from autocare.databases import vcdb, pcdb, padb, qdb, brand


class TestBaseModel:
    """Test BaseModel from_dict and extra field handling."""

    def test_from_dict_known_fields(self):
        """Test that known fields are assigned correctly."""
        data = {"EffectiveDateTime": "2024-01-01T00:00:00Z", "EndDateTime": None}
        model = VersionedModel.from_dict(data)
        assert model.EffectiveDateTime == "2024-01-01T00:00:00Z"
        assert model.EndDateTime is None
        assert model.extra == {}

    def test_from_dict_unknown_fields_go_to_extra(self):
        """Test that unknown fields are stored in extra."""
        data = {
            "EffectiveDateTime": "2024-01-01T00:00:00Z",
            "SomeNewField": "value",
            "AnotherField": 42,
        }
        model = VersionedModel.from_dict(data)
        assert model.EffectiveDateTime == "2024-01-01T00:00:00Z"
        assert model.extra == {"SomeNewField": "value", "AnotherField": 42}

    def test_from_dict_empty(self):
        """Test from_dict with empty dict."""
        model = BaseModel.from_dict({})
        assert model.extra == {}

    def test_cultured_model_includes_culture(self):
        """Test CulturedModel has CultureID field."""
        data = {"CultureID": "en-US", "EffectiveDateTime": "2024-01-01T00:00:00Z"}
        model = CulturedModel.from_dict(data)
        assert model.CultureID == "en-US"
        assert model.EffectiveDateTime == "2024-01-01T00:00:00Z"

    def test_extra_default_factory(self):
        """Test that extra field uses default_factory (no shared state)."""
        m1 = BaseModel()
        m2 = BaseModel()
        m1.extra["key"] = "value"
        assert "key" not in m2.extra


class TestVCdbModels:
    """Test VCdb models."""

    def test_tables_constant(self):
        """Test TABLES constant is populated."""
        assert "Vehicle" in vcdb.TABLES
        assert "BaseVehicle" in vcdb.TABLES
        assert "EngineConfig" in vcdb.TABLES
        assert "Make" in vcdb.TABLES
        assert "Model" in vcdb.TABLES
        assert len(vcdb.TABLES) > 50

    def test_vehicle_from_dict(self):
        """Test Vehicle model from real API shape."""
        data = {
            "VehicleID": 1,
            "BaseVehicleID": 1,
            "SubModelID": 1,
            "RegionID": 1,
            "PublicationStageID": 4,
            "EffectiveDateTime": "2017-04-21T13:21:29Z",
            "EndDateTime": None,
        }
        v = vcdb.Vehicle.from_dict(data)
        assert v.VehicleID == 1
        assert v.BaseVehicleID == 1
        assert v.SubModelID == 1
        assert v.RegionID == 1
        assert v.PublicationStageID == 4
        assert v.EffectiveDateTime == "2017-04-21T13:21:29Z"
        assert v.EndDateTime is None
        assert v.extra == {}

    def test_base_vehicle_from_dict(self):
        """Test BaseVehicle model from real API shape."""
        data = {
            "BaseVehicleID": 1,
            "YearID": 2002,
            "MakeID": 1,
            "ModelID": 1,
            "EffectiveDateTime": "2017-04-21T13:14:04Z",
            "EndDateTime": None,
        }
        bv = vcdb.BaseVehicle.from_dict(data)
        assert bv.BaseVehicleID == 1
        assert bv.YearID == 2002
        assert bv.MakeID == 1

    def test_make_from_dict(self):
        """Test Make model with CultureID."""
        data = {
            "MakeID": 1,
            "MakeName": "Suzuki",
            "CultureID": "en-US",
            "EffectiveDateTime": "2017-04-21T13:13:05",
            "EndDateTime": None,
        }
        m = vcdb.Make.from_dict(data)
        assert m.MakeID == 1
        assert m.MakeName == "Suzuki"
        assert m.CultureID == "en-US"

    def test_engine_config_from_dict(self):
        """Test EngineConfig model from real API shape."""
        data = {
            "EngineConfigID": 37,
            "EngineDesignationID": 1,
            "EngineVINID": 14,
            "ValvesID": 2,
            "EngineBaseID": 19,
            "FuelDeliveryConfigID": 8,
            "AspirationID": 6,
            "CylinderHeadTypeID": 5,
            "FuelTypeID": 5,
            "IgnitionSystemTypeID": 5,
            "EngineMfrID": 7,
            "EngineVersionID": 3,
            "PowerOutputID": 1239,
            "EffectiveDateTime": "2023-03-30T20:41:05.977Z",
            "EndDateTime": None,
        }
        ec = vcdb.EngineConfig.from_dict(data)
        assert ec.EngineConfigID == 37
        assert ec.EngineBaseID == 19
        assert ec.PowerOutputID == 1239

    def test_vehicle_extra_captures_new_fields(self):
        """Test that new API fields are captured in extra."""
        data = {
            "VehicleID": 1,
            "BaseVehicleID": 1,
            "NewFieldFromAPI": "surprise",
        }
        v = vcdb.Vehicle.from_dict(data)
        assert v.VehicleID == 1
        assert v.extra == {"NewFieldFromAPI": "surprise"}


class TestPCdbModels:
    """Test PCdb models."""

    def test_tables_constant(self):
        """Test TABLES constant is populated."""
        assert "Parts" in pcdb.TABLES
        assert "Categories" in pcdb.TABLES
        assert len(pcdb.TABLES) == 20

    def test_part_from_dict(self):
        """Test Part model from real API shape."""
        data = {
            "PartTerminologyID": 57192,
            "PartTerminologyName": "110 Volt Accessory Power Outlet",
            "PartsDescriptionID": 12164,
            "RevDate": "2018-02-15T18:20:41.15",
            "CultureID": "en-US",
            "EffectiveDateTime": "2018-02-15T18:20:41.15",
            "EndDateTime": None,
        }
        p = pcdb.Part.from_dict(data)
        assert p.PartTerminologyID == 57192
        assert p.PartTerminologyName == "110 Volt Accessory Power Outlet"
        assert p.CultureID == "en-US"

    def test_category_from_dict(self):
        """Test Category model from real API shape."""
        data = {
            "CategoryID": 1,
            "CategoryName": "Accessories",
            "CultureID": "en-US",
            "EffectiveDateTime": "2021-08-20T19:34:00.467",
            "EndDateTime": None,
        }
        c = pcdb.Category.from_dict(data)
        assert c.CategoryID == 1
        assert c.CategoryName == "Accessories"


class TestPAdbModels:
    """Test PAdb models."""

    def test_tables_constant(self):
        """Test TABLES constant is populated."""
        assert "PartAttributes" in padb.TABLES
        assert "ValidValues" in padb.TABLES
        assert "Style" in padb.TABLES
        assert len(padb.TABLES) == 12

    def test_part_attribute_from_dict(self):
        """Test PartAttribute model from real API shape."""
        data = {
            "PAID": 10060,
            "PAName": "12 Volt Compatible",
            "PADescription": "Describes whether or not part/component is compatible.",
            "CultureID": "en-US",
            "EffectiveDateTime": "2023-03-07T16:46:33.253",
            "EndDateTime": None,
        }
        pa = padb.PartAttribute.from_dict(data)
        assert pa.PAID == 10060
        assert pa.PAName == "12 Volt Compatible"

    def test_valid_value_from_dict(self):
        """Test ValidValue model from real API shape."""
        data = {
            "ValidValueID": 5293,
            "ValidValue": "#0 - 80",
            "CultureID": "en-US",
            "EffectiveDateTime": "2025-06-02T17:49:56.61Z",
            "EndDateTime": None,
        }
        vv = padb.ValidValue.from_dict(data)
        assert vv.ValidValueID == 5293
        assert vv.ValidValue == "#0 - 80"

    def test_style_from_dict(self):
        """Test Style model from real API shape."""
        data = {
            "StyleID": 556,
            "StyleName": "Adjustable",
            "CultureID": "en-US",
            "EffectiveDateTime": "2023-08-24T19:30:04.04Z",
            "EndDateTime": None,
        }
        s = padb.Style.from_dict(data)
        assert s.StyleID == 556
        assert s.StyleName == "Adjustable"


class TestQdbModels:
    """Test Qdb models."""

    def test_tables_constant(self):
        """Test TABLES constant is populated."""
        assert "Qualifier" in qdb.TABLES
        assert len(qdb.TABLES) == 4

    def test_qualifier_from_dict(self):
        """Test Qualifier model from real API shape."""
        data = {
            "QualifierID": 1,
            "QualifierText": "CV Joint with <p1/>",
            "ExampleText": "null",
            "QualifierTypeID": 1,
            "CultureID": "en-US",
            "EffectiveDateTime": "2006-06-01T16:01:00Z",
            "EndDateTime": None,
        }
        q = qdb.Qualifier.from_dict(data)
        assert q.QualifierID == 1
        assert q.QualifierText == "CV Joint with <p1/>"
        assert q.QualifierTypeID == 1
        assert q.CultureID == "en-US"


class TestBrandModels:
    """Test Brand models."""

    def test_tables_constants(self):
        """Test table name constants."""
        assert brand.TABLES_V1 == ["Brand"]
        assert brand.TABLES_V2 == ["BrandTable"]

    def test_brand_from_dict(self):
        """Test Brand model from real API shape."""
        data = {
            "RecordID": "1",
            "ParentID": "BBBB",
            "ParentCompany": "3M",
            "BrandID": "BBBB",
            "BrandName": "3M",
            "SubBrandID": "null",
            "SubBrandName": "null",
            "BrandOEMFlag": "False",
            "EffectiveDateTime": "2007-07-12T00:00:00Z",
            "EndDateTime": None,
        }
        b = brand.Brand.from_dict(data)
        assert b.RecordID == "1"
        assert b.ParentCompany == "3M"
        assert b.BrandID == "BBBB"
        assert b.BrandName == "3M"
        assert b.BrandOEMFlag == "False"

    def test_brand_extra_field(self):
        """Test that unknown brand fields go to extra."""
        data = {
            "BrandID": "TEST",
            "BrandName": "Test",
            "NewV3Field": "future",
        }
        b = brand.Brand.from_dict(data)
        assert b.BrandID == "TEST"
        assert b.extra == {"NewV3Field": "future"}
