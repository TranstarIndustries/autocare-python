"""Base model utilities for typed API response models."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict, Optional


@dataclass
class BaseModel:
    """Base class for all typed API response models.

    Provides from_dict() classmethod that maps known fields and stores
    unknown fields in the extra attribute.
    """

    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create an instance from an API response dictionary.

        Known fields are assigned to typed attributes. Unknown fields
        are stored in the extra dict.
        """
        known_fields = {f.name for f in fields(cls) if f.name != "extra"}
        known = {}
        extra = {}

        for key, value in data.items():
            if key in known_fields:
                known[key] = value
            else:
                extra[key] = value

        return cls(**known, extra=extra)


@dataclass
class VersionedModel(BaseModel):
    """Base model for records that include versioning fields.

    Most AutoCare v2.0+ records include EffectiveDateTime and EndDateTime.
    """

    EffectiveDateTime: Optional[str] = None
    EndDateTime: Optional[str] = None


@dataclass
class CulturedModel(VersionedModel):
    """Base model for records that include CultureID.

    Tables with human-readable name fields typically include CultureID.
    """

    CultureID: Optional[str] = None
