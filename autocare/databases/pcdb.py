"""PCdb (Product Classification Database) models and constants."""

from dataclasses import dataclass
from typing import Optional

from autocare.databases.base import CulturedModel

# Table names available in PCdb
TABLES = [
    "ACESCodedValues",
    "Alias",
    "Categories",
    "Parts",
    "PartCategory",
    "PartsDescription",
    "PartPosition",
    "PartsRelationship",
    "PartsSupersession",
    "PartsToAlias",
    "PartsToUse",
    "PIESCode",
    "PIESEXPICode",
    "PIESEXPIGroup",
    "PIESField",
    "PIESReferenceFieldCode",
    "PIESSegment",
    "Positions",
    "Subcategories",
    "Use",
]


@dataclass
class Part(CulturedModel):
    """PCdb Parts record."""

    PartTerminologyID: Optional[int] = None
    PartTerminologyName: Optional[str] = None
    PartsDescriptionID: Optional[int] = None
    RevDate: Optional[str] = None


@dataclass
class Category(CulturedModel):
    """PCdb Categories record."""

    CategoryID: Optional[int] = None
    CategoryName: Optional[str] = None


@dataclass
class Subcategory(CulturedModel):
    """PCdb Subcategories record."""

    SubcategoryID: Optional[int] = None
    SubcategoryName: Optional[str] = None
    CategoryID: Optional[int] = None


@dataclass
class Position(CulturedModel):
    """PCdb Positions record."""

    PositionID: Optional[int] = None
    PositionName: Optional[str] = None
