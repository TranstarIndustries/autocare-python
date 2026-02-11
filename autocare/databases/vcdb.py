"""VCdb (Vehicle Configuration Database) models and constants."""

from dataclasses import dataclass
from typing import Optional

from autocare.databases.base import CulturedModel, VersionedModel

# Table names available in VCdb
TABLES = [
    "Abbreviation",
    "Aspiration",
    "BaseVehicle",
    "BedConfig",
    "BedLength",
    "BedType",
    "BodyNumDoors",
    "BodyStyleConfig",
    "BodyType",
    "BrakeABS",
    "BrakeConfig",
    "BrakeSystem",
    "BrakeType",
    "Class",
    "CylinderHeadType",
    "DriveType",
    "ElecControlled",
    "EngineBase",
    "EngineBase2",
    "EngineBlock",
    "EngineBoreStroke",
    "EngineConfig",
    "EngineConfig2",
    "EngineDesignation",
    "EngineVersion",
    "EngineVIN",
    "FuelDeliveryConfig",
    "FuelDeliverySubType",
    "FuelDeliveryType",
    "FuelSystemControlType",
    "FuelSystemDesign",
    "FuelType",
    "IgnitionSystemType",
    "Make",
    "Mfr",
    "MfrBodyCode",
    "Model",
    "PowerOutput",
    "PublicationStage",
    "Region",
    "SpringType",
    "SpringTypeConfig",
    "SteeringConfig",
    "SteeringSystem",
    "SteeringType",
    "SubModel",
    "Transmission",
    "TransmissionBase",
    "TransmissionControlType",
    "TransmissionMfrCode",
    "TransmissionNumSpeeds",
    "TransmissionType",
    "Valves",
    "Vehicle",
    "VehicleToBedConfig",
    "VehicleToBodyConfig",
    "VehicleToBodyStyleConfig",
    "VehicleToBrakeConfig",
    "VehicleToClass",
    "VehicleToDriveType",
    "VehicleToEngineConfig",
    "VehicleToMfrBodyCode",
    "VehicleToSpringTypeConfig",
    "VehicleToSteeringConfig",
    "VehicleToTransmission",
    "VehicleToWheelBase",
    "VehicleType",
    "VehicleTypeGroup",
    "WheelBase",
    "Year",
]


@dataclass
class Vehicle(VersionedModel):
    """VCdb Vehicle record."""

    VehicleID: Optional[int] = None
    BaseVehicleID: Optional[int] = None
    SubModelID: Optional[int] = None
    RegionID: Optional[int] = None
    PublicationStageID: Optional[int] = None


@dataclass
class BaseVehicle(VersionedModel):
    """VCdb BaseVehicle record."""

    BaseVehicleID: Optional[int] = None
    YearID: Optional[int] = None
    MakeID: Optional[int] = None
    ModelID: Optional[int] = None


@dataclass
class Make(CulturedModel):
    """VCdb Make record."""

    MakeID: Optional[int] = None
    MakeName: Optional[str] = None


@dataclass
class Model(CulturedModel):
    """VCdb Model record."""

    ModelID: Optional[int] = None
    ModelName: Optional[str] = None
    VehicleTypeID: Optional[int] = None


@dataclass
class EngineConfig(VersionedModel):
    """VCdb EngineConfig record."""

    EngineConfigID: Optional[int] = None
    EngineDesignationID: Optional[int] = None
    EngineVINID: Optional[int] = None
    ValvesID: Optional[int] = None
    EngineBaseID: Optional[int] = None
    FuelDeliveryConfigID: Optional[int] = None
    AspirationID: Optional[int] = None
    CylinderHeadTypeID: Optional[int] = None
    FuelTypeID: Optional[int] = None
    IgnitionSystemTypeID: Optional[int] = None
    EngineMfrID: Optional[int] = None
    EngineVersionID: Optional[int] = None
    PowerOutputID: Optional[int] = None


@dataclass
class Year(VersionedModel):
    """VCdb Year record."""

    YearID: Optional[int] = None


@dataclass
class SubModel(CulturedModel):
    """VCdb SubModel record."""

    SubModelID: Optional[int] = None
    SubModelName: Optional[str] = None
