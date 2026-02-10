"""Qdb (Qualifier Database) models and constants."""

from dataclasses import dataclass
from typing import Optional

from autocare.databases.base import CulturedModel

# Table names available in Qdb
TABLES = [
    "GroupNumber",
    "Qualifier",
    "QualifierGroup",
    "QualifierType",
]


@dataclass
class Qualifier(CulturedModel):
    """Qdb Qualifier record."""

    QualifierID: Optional[int] = None
    QualifierText: Optional[str] = None
    ExampleText: Optional[str] = None
    QualifierTypeID: Optional[int] = None


@dataclass
class QualifierType(CulturedModel):
    """Qdb QualifierType record."""

    QualifierTypeID: Optional[int] = None
    QualifierTypeName: Optional[str] = None
