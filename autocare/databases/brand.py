"""Brand Table models and constants."""

from dataclasses import dataclass
from typing import Optional

from autocare.databases.base import VersionedModel

# Table names available in Brand database
TABLES_V1 = ["Brand"]
TABLES_V2 = ["BrandTable"]


@dataclass
class Brand(VersionedModel):
    """Brand Table record."""

    RecordID: Optional[str] = None
    ParentID: Optional[str] = None
    ParentCompany: Optional[str] = None
    BrandID: Optional[str] = None
    BrandName: Optional[str] = None
    SubBrandID: Optional[str] = None
    SubBrandName: Optional[str] = None
    BrandOEMFlag: Optional[str] = None
