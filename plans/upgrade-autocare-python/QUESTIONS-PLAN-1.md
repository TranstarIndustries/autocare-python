# Plan Critique Questions

## 1. Integration test timing

The plan currently places integration tests at Step 8 (near the end). The URL routing fix in Step 2 is the highest-risk change and would benefit from immediate validation against real endpoints. Should I:

- **(A)** Move a basic integration test (auth + fetch from each database) to right after Step 2, with the full integration suite still at Step 8?
- **(B)** Keep integration tests at Step 8 and rely on mock-based URL assertion tests for Step 2?
    option A.

## 2. Deprecation of explicit `version` parameter

`fetch_records` currently has `version: str = "1.0"`. After Step 1, `api_versions` provides per-database defaults. The `version` param creates ambiguity — which takes precedence? Options:

- **(A)** Keep `version` param but make it `Optional[str] = None`. When `None`, use `api_versions[db_name]`. When explicitly provided, it overrides. Log a deprecation warning if the explicit param is used.
- **(B)** Remove the `version` param entirely (breaking change) — callers must use `api_versions`.
- **(C)** Keep `version` param as-is for backward compatibility, but change its default to `None` so `api_versions` is used by default.
    Probably A or C, since they aren't breaking changes. What do you recommend as the best practice and most intuitive?

## 3. Typed model design — strict or lenient?

When the API returns fields not present in our dataclass, should `from_dict`:

- **(A)** Silently ignore unknown fields (lenient — safer against API additions)?
- **(B)** Raise an error on unknown fields (strict — catches schema drift)?
- **(C)** Store unknown fields in an `extra: Dict[str, Any]` attribute (hybrid)?
    Probably C, but you tell me what's best practice.
