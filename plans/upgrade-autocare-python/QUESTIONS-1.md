# Questions - Round 1

## Scope & Priority

1. **Which phases from the update plan are in scope for this feature branch?**
   The analysis doc describes three phases:
   - Phase 1: Multi-version support (`api_versions` parameter on `AutoCareAPI`)
   - Phase 2: Database-specific submodules (`autocare/vcdb/`, `autocare/aces/`, etc.)
   - Phase 3: Field mapping/compatibility layer (`autocare/compatibility/field_mapping.py`)

   Should we implement all three, or just Phase 1 (multi-version support) for now? Phase 2 and 3 introduce parsers and models that seem to depend on having actual API access to validate against.


   Let's implement all three, I have API access now (see .env file).

2. **What is the target version number?** The doc suggests `v0.2.0`. Should we use that?

   Yes.

## Multi-Version Support (Phase 1 specifics)

3. **BASE_URL currently hardcodes `v1.0`:**
   ```python
   BASE_URL = "https://common.autocarevip.com/api/v1.0"
   ```
   The `fetch_records` method constructs per-database URLs with a version parameter:
   ```python
   f"https://{db_name}.autocarevip.com/api/v{version}/{db_name}/{table_name}"
   ```
   But `list_databases` and `list_tables` use the hardcoded `BASE_URL`. Should those also respect per-database versioning, or do they always use the common v1.0 endpoint?

   I'm not sure, we'll probably have to test it to make sure. Or you'll have to search the autocare API docs to confirm, I just added all the API docs to `docs/autocare-api` so you can review.

4. **Default versions:** When `api_versions` is not supplied, should the defaults be the *current* versions (VCdb 1.0, ACES 4.2, PIES 7.2, etc.) or the *new* versions (VCdb 2.0, ACES 5.0, PIES 8.0)?

   Default to new versions.

5. **PCdb version:** The doc says "PCdb not changing" and shows `"pcdb": "1.0"` in the example. Is PCdb staying at 1.0, or is there a version bump we need to account for?
   I'm not sure, but you can check `docs/autocare-api`.

## Database-Specific Modules (Phase 2 specifics)

6. **What goes in the version-specific modules?** The doc shows `vcdb/v1.py`, `vcdb/v2.py`, `aces/v4.py`, `aces/v5.py`, etc. What should these contain?
   - Data models / Pydantic models for the API response schemas?
   - Parser logic for XML (ACES/PIES)?
   - Just constant definitions (table names, field names)?

   The current client returns raw `Dict[str, Any]` — are we introducing typed response models, or keeping the dict-based interface?
   Introduce typed response models.

7. **ACES/PIES parsers:** The doc mentions ACES/PIES XML parsing, but the current client is purely a REST JSON API client. Is XML parsing in scope here, or is that for a different tool/pipeline?
   XML parsing not in scope, unless we need the client to be able to be able to handle ACES/PIES queries.

## Compatibility Layer (Phase 3 specifics)

8. **Who consumes the field mapping?** Is `migrate_aces_record()` intended for:
   - Internal use within the client (transparently mapping old field names to new)?
   - External use by consumers who have existing data in old formats?
   - Both?
   Let's assume both.

## Testing & Validation

9. **Do we have access to the new API versions for testing?** The doc says PIES 8.0 is already live, and VCdb 2.0/ACES 5.0 go live 1/28/2026 (which has passed). Can we test against real endpoints, or should tests remain mock-based?
   Keep the mocks for fast unit tests, but yes let's add some tests that test against real endpoints (i.e. integration tests).

10. **Breaking changes to existing tests:** Changing `BASE_URL` or constructor signature could break existing tests. Should we maintain backward compatibility with the current constructor signature (no `api_versions` required), defaulting to current behavior?
   Yes, maintain the old set of tests so we can confirm the old API tests can still pass.
