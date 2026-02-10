# autocare-python v0.2.0 Upgrade Plan

**Overall Progress:** `0%`

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
- **Typed models — unknown fields:** Store in `extra: Dict[str, Any]` attribute via `from_dict()`. Known fields get typed access, unknown fields are preserved without data loss.
- **`from_dict()` classmethod:** Defined on each model in Step 3 (database modules), wired into client in Step 4.
- **`create_client` factory:** Updated to forward `api_versions` kwarg.

---

## Tasks

- [ ] 🟥 **Step 1: Add multi-version support to AutoCareAPI**
  - [ ] 🟥 Write failing tests for `api_versions` constructor param with defaults
  - [ ] 🟥 Add `api_versions` param to `__init__` (optional, backward-compatible)
  - [ ] 🟥 Store `api_versions` dict with defaults; expose `get_version(db_name)` helper
  - [ ] 🟥 Change `fetch_records` `version` param default from `"1.0"` to `None`; when `None`, resolve from `api_versions`
  - [ ] 🟥 Update `create_client` to forward `api_versions`
  - [ ] 🟥 Verify existing tests still pass (no breaking changes)
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 2: Fix database-specific URL routing**
  - [ ] 🟥 Write failing tests for correct URL generation per database (PAdb → pcdb subdomain, Brand → brand subdomain)
  - [ ] 🟥 Add subdomain mapping constant (`DATABASE_SUBDOMAINS`)
  - [ ] 🟥 Add URL path mapping for databases with non-standard patterns (Brand Table)
  - [ ] 🟥 Refactor `fetch_records` to use mappings + `api_versions`
  - [ ] 🟥 Log constructed URL at debug level for troubleshooting
  - [ ] 🟥 Verify existing tests still pass
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 2b: Basic integration smoke test**
  - [ ] 🟥 Create `tests/test_integration.py` with `@pytest.mark.integration` marker (skipped in CI)
  - [ ] 🟥 Test auth + `list_databases` with real credentials
  - [ ] 🟥 Test `fetch_records` with `limit=1` against each database (vcdb, pcdb, padb, qdb, brand) to validate URL routing
  - [ ] 🟥 Run manually to confirm; fix any URL issues before proceeding
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 3: Create database-specific modules with typed response models**
  - [ ] 🟥 Create `autocare/databases/` package with `__init__.py`
  - [ ] 🟥 Create `autocare/databases/vcdb.py` — table names, field definitions, and typed dataclass models for v1.0 and v2.0 (e.g. `Vehicle`, `BaseVehicle`, `EngineConfig`). Each model has `from_dict(cls, data)` classmethod; unknown fields stored in `extra: Dict[str, Any]`.
  - [ ] 🟥 Create `autocare/databases/pcdb.py` — table names, field definitions, and typed models for v1.0 (e.g. `PartTerminology`, `Category`)
  - [ ] 🟥 Create `autocare/databases/padb.py` — table names, field definitions, and typed models for v4.0 and v5.0 (e.g. `ProductAttribute`, `ValidValue`)
  - [ ] 🟥 Create `autocare/databases/qdb.py` — table names, field definitions, and typed models for v1.0 and v2.0 (e.g. `Qualifier`)
  - [ ] 🟥 Create `autocare/databases/brand.py` — field definitions and typed models for v1.0 and v2.0 (e.g. `Brand`)
  - [ ] 🟥 Write tests for database module constants, model construction, `from_dict` parsing, and `extra` field capture
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 4: Add typed record fetching to AutoCareAPI**
  - [ ] 🟥 Write failing tests for `fetch_records` returning typed models when a `model` kwarg is provided
  - [ ] 🟥 Add optional `model` parameter to `fetch_records` / `fetch_all_records` — when provided, each dict is passed to `model.from_dict()` before yielding
  - [ ] 🟥 When `model` is `None` (default), return raw `Dict[str, Any]` as before (backward compat)
  - [ ] 🟥 Verify existing tests still pass (raw dict path unchanged)
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 5: Create ACES/PIES version modules**
  - [ ] 🟥 Create `autocare/standards/` package with `__init__.py`
  - [ ] 🟥 Create `autocare/standards/aces.py` — ACES 4.2 and 5.0 element/attribute name constants, breaking change definitions
  - [ ] 🟥 Create `autocare/standards/pies.py` — PIES 7.2 and 8.0 segment constants, new PackagingItems definitions
  - [ ] 🟥 Write tests for standards module constants
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 6: Implement field mapping / compatibility layer**
  - [ ] 🟥 Write failing tests for `migrate_aces_record` (4.2 → 5.0, 5.0 → 4.2)
  - [ ] 🟥 Write failing tests for `migrate_vcdb_record` (1.0 → 2.0)
  - [ ] 🟥 Write failing tests for `migrate_padb_record` (4.0 → 5.0)
  - [ ] 🟥 Create `autocare/compatibility/` package with `__init__.py`
  - [ ] 🟥 Create `autocare/compatibility/field_mapping.py` with mapping dicts and migration functions
  - [ ] 🟥 Verify all migration functions pass tests
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 7: Update package exports**
  - [ ] 🟥 Update `autocare/__init__.py` to export new modules and key symbols
  - [ ] 🟥 Ensure `from autocare import AutoCareAPI` still works (backward compat)
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 8: Full integration test suite**
  - [ ] 🟥 Expand `tests/test_integration.py` with typed model tests against real API
  - [ ] 🟥 Test `fetch_records` with `model=` kwarg for each database
  - [ ] 🟥 Validate that `from_dict` handles real API response shapes (catch field mismatches)
  - [ ] 🟥 Test field mapping functions with real fetched records
  - [ ] 🟥 Update PLAN.md

- [ ] 🟥 **Step 9: Release prep**
  - [ ] 🟥 Bump version to 0.2.0 in `pyproject.toml`
  - [ ] 🟥 Update `CHANGELOG.md` with v0.2.0 entries
  - [ ] 🟥 Run full validation (`just validate`)
  - [ ] 🟥 Update PLAN.md with final status

## Deferred Items

(Items moved here only with user approval)

- None
