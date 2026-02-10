# autocare-python v0.2.0 Upgrade Plan

**Overall Progress:** `100%` ✅

**Original Prompt:** [PROMPT.md](./PROMPT.md)
**Questions:** [QUESTIONS-1.md](./QUESTIONS-1.md)
**Plan Critique:** [QUESTIONS-PLAN-1.md](./QUESTIONS-PLAN-1.md)

## Summary

Upgrade the autocare-python package from v0.1.0 to v0.2.0 with multi-version API support, database-specific modules, typed response models, and a field mapping/compatibility layer for migrating between API versions.

### Key Findings from API Docs

- `list_databases` / `list_tables` always use `https://common.autocarevip.com/api/v1.0/...` (no versioning)
- Record fetching uses per-database subdomains: `https://{subdomain}.autocarevip.com/api/v{v}/{db_name}/{table}`
- **Bug in current code:** PAdb shares `pcdb` subdomain, not `padb`. Brand Table uses `brand` subdomain with no table path segment.
- PCdb stays at 1.0 until 3/26/2026

### Default Versions (v0.2.0)

| Database | Default Version |
|----------|----------------|
| vcdb     | 2.0            |
| pcdb     | 1.0            |
| padb     | 5.0            |
| qdb      | 2.0            |
| brand    | 2.0            |

### Design Decisions

- **`version` param on `fetch_records`:** Change default from `"1.0"` to `None`. When `None`, use `api_versions[db_name]`. When explicitly provided, it overrides. No deprecation warning — the explicit param remains useful for one-off overrides.
- **Typed models — unknown fields:** Store in `extra: Dict[str, Any]` attribute using `@dataclass` with `extra: Dict[str, Any] = field(default_factory=dict)`. Known fields get typed access, unknown fields are preserved without data loss via `from_dict()`.
- **`from_dict()` classmethod:** Defined on each model in Step 3 (database modules), wired into client in Step 4.
- **`create_client` factory:** Updated to forward `api_versions` kwarg.

---

## Tasks

- [x] 🟩 **Step 1: Add multi-version support to AutoCareAPI**
  - [x] 🟩 Write failing tests for `api_versions` constructor param with defaults
  - [x] 🟩 Add `api_versions` param to `__init__` (optional, backward-compatible)
  - [x] 🟩 Store `api_versions` dict with defaults; expose `get_version(db_name)` helper
  - [x] 🟩 Change `fetch_records` `version` param default from `"1.0"` to `None`; when `None`, resolve from `api_versions`
  - [x] 🟩 Update `create_client` to forward `api_versions` (already works via `**kwargs`)
  - [x] 🟩 Verify existing tests still pass (37 passed, 1 skipped)
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 2: Fix database-specific URL routing**
  - [x] 🟩 Write failing tests for correct URL generation per database (PAdb → pcdb subdomain, Brand → brand subdomain)
  - [x] 🟩 Add subdomain mapping constant (`DATABASE_SUBDOMAINS`)
  - [x] 🟩 Add URL path mapping for databases with non-standard patterns (`DATABASE_NO_TABLE_SEGMENT`)
  - [x] 🟩 Add `_build_record_url` helper; refactor `fetch_records` to use it
  - [x] 🟩 Log constructed URL at debug level for troubleshooting
  - [x] 🟩 Verify existing tests still pass (43 passed, 1 skipped)
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 2b: Basic integration smoke test**
  - [x] 🟩 Create `tests/test_integration.py` with `@pytest.mark.integration` marker (skipped in CI)
  - [x] 🟩 Test auth + `list_databases` with real credentials
  - [x] 🟩 Test `fetch_records` with `limit=1` against each database (vcdb, pcdb, padb, qdb, brand)
  - [x] 🟩 Discovered Brand v1.0 uses `brand/Brand`, v2.0 uses `brand/BrandTable` — standard URL pattern works
  - [x] 🟩 Removed `DATABASE_NO_TABLE_SEGMENT` — not needed
  - [x] 🟩 All 8 integration tests pass
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 3: Create database-specific modules with typed response models**
  - [x] 🟩 Create `autocare/databases/` package with `__init__.py`
  - [x] 🟩 Create `autocare/databases/base.py` — `BaseModel` with `from_dict()` classmethod and `extra: Dict[str, Any] = field(default_factory=dict)`, plus `VersionedModel` and `CulturedModel`
  - [x] 🟩 Create `autocare/databases/vcdb.py` — 70 table names, `Vehicle`, `BaseVehicle`, `Make`, `Model`, `EngineConfig`, `Year`, `SubModel` dataclass models
  - [x] 🟩 Create `autocare/databases/pcdb.py` — 20 table names, `Part`, `Category`, `Subcategory`, `Position` models
  - [x] 🟩 Create `autocare/databases/padb.py` — 12 table names, `PartAttribute`, `ValidValue`, `Style`, `PartAttributeAssignment` models
  - [x] 🟩 Create `autocare/databases/qdb.py` — 4 table names, `Qualifier`, `QualifierType` models
  - [x] 🟩 Create `autocare/databases/brand.py` — `TABLES_V1`, `TABLES_V2`, `Brand` model
  - [x] 🟩 Write tests for database module constants, model construction, `from_dict` parsing, and `extra` field capture (23 tests)
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 4: Add typed record fetching to AutoCareAPI**
  - [x] 🟩 Write failing tests for `fetch_records` returning typed models when a `model` kwarg is provided
  - [x] 🟩 Add optional `model` parameter to `fetch_records` / `fetch_all_records` — when provided, each dict is passed to `model.from_dict()` before yielding
  - [x] 🟩 When `model` is `None` (default), return raw `Dict[str, Any]` as before (backward compat)
  - [x] 🟩 Verify existing tests still pass (70 passed, 1 skipped)
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 5: Create ACES/PIES version modules**
  - [x] 🟩 Create `autocare/standards/` package with `__init__.py`
  - [x] 🟩 Create `autocare/standards/aces.py` — ACES 4.2 and 5.0 element constants, `V4_TO_V5_FIELD_RENAMES`, `V5_REMOVED_ELEMENTS`, `V5_NEW_ELEMENTS`
  - [x] 🟩 Create `autocare/standards/pies.py` — PIES 7.2 and 8.0 segment codes, `V8_NEW_SEGMENTS`, backward compat confirmed
  - [x] 🟩 Write tests for standards module constants (16 tests)
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 6: Implement field mapping / compatibility layer**
  - [x] 🟩 Write failing tests for `migrate_aces_record` (4.2 → 5.0, 5.0 → 4.2)
  - [x] 🟩 Write failing tests for `migrate_vcdb_record` (1.0 → 2.0, 2.0 → 1.0)
  - [x] 🟩 Write failing tests for `migrate_padb_record` (4.0 → 5.0, 5.0 → 4.0)
  - [x] 🟩 Create `autocare/compatibility/` package with `__init__.py`
  - [x] 🟩 Create `autocare/compatibility/field_mapping.py` with mapping dicts and migration functions
  - [x] 🟩 Verify all migration functions pass tests (13 tests)
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 7: Update package exports**
  - [x] 🟩 Update `autocare/__init__.py` to export new modules and key symbols
  - [x] 🟩 Ensure `from autocare import AutoCareAPI` still works (backward compat)
  - [x] 🟩 Verify all tests pass (99 passed, 1 skipped)
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 8: Full integration test suite**
  - [x] 🟩 Expand `tests/test_integration.py` with `TestIntegrationTypedModels` class (7 tests)
  - [x] 🟩 Test `fetch_records` with `model=` kwarg for each database (Vehicle, Make, Part, PartAttribute, Qualifier, Brand)
  - [x] 🟩 Validate that `from_dict` handles real API response shapes
  - [x] 🟩 Add `TestIntegrationFieldMapping` class — test `migrate_vcdb_record` with real v2.0 records (2 tests)
  - [x] 🟩 All 17 integration tests pass against real API
  - [x] 🟩 Update PLAN.md

- [x] 🟩 **Step 9: Release prep**
  - [x] 🟩 Bump version to 0.2.0 in `pyproject.toml`
  - [x] 🟩 Update `CHANGELOG.md` with v0.2.0 entries
  - [x] 🟩 Run full validation: ruff format, ruff check, mypy (0 issues), pytest (99 passed, 1 skipped)
  - [x] 🟩 Update PLAN.md with final status

## Deferred Items

(Items moved here only with user approval)

- None
