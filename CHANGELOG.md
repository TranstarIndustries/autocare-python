# Changelog

All notable changes to the transend-python project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-10

### Added
- Multi-version API support via `api_versions` constructor parameter with per-database version defaults (VCdb 2.0, PCdb 1.0, PAdb 5.0, Qdb 2.0, Brand 2.0)
- `get_version()` helper method for resolving database API versions
- Database-specific modules (`autocare.databases`) with typed dataclass models for VCdb, PCdb, PAdb, Qdb, and Brand
- `BaseModel` with `from_dict()` classmethod and `extra` field for forward-compatible API response parsing
- Optional `model` parameter on `fetch_records()` and `fetch_all_records()` for typed record fetching
- ACES/PIES standards modules (`autocare.standards`) with version constants and breaking change definitions
- Field mapping compatibility layer (`autocare.compatibility`) with `migrate_aces_record`, `migrate_vcdb_record`, and `migrate_padb_record`
- Integration test suite validating all databases against real API endpoints
- Package-level exports in `autocare/__init__.py`

### Fixed
- PAdb URL routing now correctly uses `pcdb` subdomain instead of `padb`
- Database-specific URL construction via `_build_record_url()` with `DATABASE_SUBDOMAINS` mapping

### Changed
- `fetch_records()` `version` parameter default changed from `"1.0"` to `None` (resolves from `api_versions`)
- `fetch_all_records()` `version` parameter default changed from `"1.0"` to `None`

## [0.1.0] - 2025-07-25

### Added
- Initial release of the Autocare Python API client
- GitHub Actions workflows for automated testing and PyPI publishing
- Basic test suite using pytest
- Documentation in README.md for installation and usage

[0.2.0]: https://github.com/TranstarIndustries/autocare-python/releases/tag/v0.2.0
[0.1.0]: https://github.com/TranstarIndustries/autocare-python/releases/tag/v0.1.0
