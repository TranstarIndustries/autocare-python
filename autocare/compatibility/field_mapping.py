"""Field mapping functions for migrating records between API versions.

Provides migrate_*_record() functions for ACES, VCdb, and PAdb that
rename fields and add/strip versioning metadata as needed.
"""

from typing import Any, Dict

from autocare.standards.aces import V4_TO_V5_FIELD_RENAMES, V5_TO_V4_FIELD_RENAMES

# Fields added in VCdb 2.0 / PAdb 5.0 that don't exist in earlier versions
_VERSIONING_FIELDS = {"EffectiveDateTime", "EndDateTime", "CultureID"}

_ACES_VERSIONS = {"4.2", "5.0"}
_VCDB_VERSIONS = {"1.0", "2.0"}
_PADB_VERSIONS = {"4.0", "5.0"}


def _rename_fields(record: Dict[str, Any], renames: Dict[str, str]) -> Dict[str, Any]:
    """Apply field renames to a record dict.

    Returns a new dict with renamed keys. Fields not in the rename map
    are copied as-is.
    """
    result = {}
    for key, value in record.items():
        new_key = renames.get(key, key)
        result[new_key] = value
    return result


def migrate_aces_record(
    record: Dict[str, Any],
    from_version: str,
    to_version: str,
) -> Dict[str, Any]:
    """Migrate an ACES record between versions.

    Supports 4.2 <-> 5.0 field renames (Part -> PartNumber, etc.).

    Args:
        record: Source record dict
        from_version: Source ACES version ("4.2" or "5.0")
        to_version: Target ACES version ("4.2" or "5.0")

    Returns:
        New dict with fields renamed for the target version

    Raises:
        ValueError: If either version is unsupported
    """
    if from_version not in _ACES_VERSIONS or to_version not in _ACES_VERSIONS:
        raise ValueError(
            f"Unsupported ACES version: {from_version} -> {to_version}. "
            f"Supported: {sorted(_ACES_VERSIONS)}"
        )

    if from_version == to_version:
        return dict(record)

    if from_version == "4.2" and to_version == "5.0":
        return _rename_fields(record, V4_TO_V5_FIELD_RENAMES)
    else:  # 5.0 -> 4.2
        return _rename_fields(record, V5_TO_V4_FIELD_RENAMES)


def migrate_vcdb_record(
    record: Dict[str, Any],
    from_version: str,
    to_version: str,
) -> Dict[str, Any]:
    """Migrate a VCdb record between versions.

    1.0 -> 2.0: Adds EffectiveDateTime, EndDateTime, CultureID (as None)
    2.0 -> 1.0: Strips EffectiveDateTime, EndDateTime, CultureID

    Args:
        record: Source record dict
        from_version: Source VCdb version ("1.0" or "2.0")
        to_version: Target VCdb version ("1.0" or "2.0")

    Returns:
        New dict with fields adjusted for the target version

    Raises:
        ValueError: If either version is unsupported
    """
    if from_version not in _VCDB_VERSIONS or to_version not in _VCDB_VERSIONS:
        raise ValueError(
            f"Unsupported VCdb version: {from_version} -> {to_version}. "
            f"Supported: {sorted(_VCDB_VERSIONS)}"
        )

    if from_version == to_version:
        return dict(record)

    result = dict(record)

    if from_version == "1.0" and to_version == "2.0":
        # Add versioning fields if not present
        for field in _VERSIONING_FIELDS:
            if field not in result:
                result[field] = None
    else:  # 2.0 -> 1.0
        # Strip versioning fields
        for field in _VERSIONING_FIELDS:
            result.pop(field, None)

    return result


def migrate_padb_record(
    record: Dict[str, Any],
    from_version: str,
    to_version: str,
) -> Dict[str, Any]:
    """Migrate a PAdb record between versions.

    4.0 -> 5.0: Adds EffectiveDateTime, EndDateTime, CultureID (as None)
    5.0 -> 4.0: Strips EffectiveDateTime, EndDateTime, CultureID

    Args:
        record: Source record dict
        from_version: Source PAdb version ("4.0" or "5.0")
        to_version: Target PAdb version ("4.0" or "5.0")

    Returns:
        New dict with fields adjusted for the target version

    Raises:
        ValueError: If either version is unsupported
    """
    if from_version not in _PADB_VERSIONS or to_version not in _PADB_VERSIONS:
        raise ValueError(
            f"Unsupported PAdb version: {from_version} -> {to_version}. "
            f"Supported: {sorted(_PADB_VERSIONS)}"
        )

    if from_version == to_version:
        return dict(record)

    result = dict(record)

    if from_version == "4.0" and to_version == "5.0":
        for field in _VERSIONING_FIELDS:
            if field not in result:
                result[field] = None
    else:  # 5.0 -> 4.0
        for field in _VERSIONING_FIELDS:
            result.pop(field, None)

    return result
