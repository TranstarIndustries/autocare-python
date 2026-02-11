"""AutoCare API client library."""

from autocare.client import (
    AutoCareAPI,
    create_client,
    AutoCareError,
    AuthenticationError,
    APIConnectionError,
    APIResponseError,
    DataValidationError,
    PaginationError,
    DatabaseInfo,
    TableInfo,
    APIResponse,
)

from autocare.databases import vcdb, pcdb, padb, qdb, brand
from autocare.databases.base import BaseModel, VersionedModel, CulturedModel

from autocare.standards import aces, pies

from autocare.compatibility.field_mapping import (
    migrate_aces_record,
    migrate_vcdb_record,
    migrate_padb_record,
)

__all__ = [
    # Client
    "AutoCareAPI",
    "create_client",
    # Exceptions
    "AutoCareError",
    "AuthenticationError",
    "APIConnectionError",
    "APIResponseError",
    "DataValidationError",
    "PaginationError",
    # Data classes
    "DatabaseInfo",
    "TableInfo",
    "APIResponse",
    # Base models
    "BaseModel",
    "VersionedModel",
    "CulturedModel",
    # Database modules
    "vcdb",
    "pcdb",
    "padb",
    "qdb",
    "brand",
    # Standards modules
    "aces",
    "pies",
    # Compatibility
    "migrate_aces_record",
    "migrate_vcdb_record",
    "migrate_padb_record",
]
