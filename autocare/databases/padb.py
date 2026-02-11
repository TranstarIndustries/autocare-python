"""PAdb (Product Attribute Database) models and constants."""

from dataclasses import dataclass
from typing import Optional

from autocare.databases.base import CulturedModel

# Table names available in PAdb
TABLES = [
    "MeasurementGroup",
    "MetaData",
    "MetaUOMCodeAssignment",
    "MetaUOMCodes",
    "PartAttributeAssignment",
    "PartAttributes",
    "PartAttributeStyle",
    "PartTerminologyStyle",
    "PartTypeStyle",
    "Style",
    "ValidValueAssignment",
    "ValidValues",
]


@dataclass
class PartAttribute(CulturedModel):
    """PAdb PartAttributes record."""

    PAID: Optional[int] = None
    PAName: Optional[str] = None
    PADescription: Optional[str] = None


@dataclass
class ValidValue(CulturedModel):
    """PAdb ValidValues record."""

    ValidValueID: Optional[int] = None
    ValidValue: Optional[str] = None


@dataclass
class Style(CulturedModel):
    """PAdb Style record."""

    StyleID: Optional[int] = None
    StyleName: Optional[str] = None


@dataclass
class PartAttributeAssignment(CulturedModel):
    """PAdb PartAttributeAssignment record."""

    PartTerminologyID: Optional[int] = None
    PAID: Optional[int] = None
    StyleID: Optional[int] = None
