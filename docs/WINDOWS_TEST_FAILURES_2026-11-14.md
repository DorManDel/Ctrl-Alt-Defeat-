# First real Windows pre-push failures — 2026-11-14

**Observed:** 28 passes, 3 errors out of 31 tests. The failures were `test_compare`, `test_preview_does_not_write`, and `test_small_write_verify_and_cleanup`.

## Root causes

1. SQLite's connection context manager is **not** a connection closer. Windows locked `test.db` when `TemporaryDirectory` tried to delete it. We now use a dedicated connection context manager that closes the handle in `finally`.
2. Capacity tests ran their fixtures under Windows `%TEMP%` on `C:`. The application correctly rejects capacity writes to the system drive. Tests now mock only the drive classification to simulate an external drive, in a disposable 1 MiB sandbox.
3. Added a regression test to ensure the production system-drive refusal remains effective. No change to the production default reserve or test-size limit.

## Validation

- Local Python tests: **32 passed** (non-Windows environment).
- On-Windows rerun: **not yet verified**.
- Windows UAC and UI manual smoke test: **pending**.

**Policy:** Treat `dev` as experimental; do not merge to `main` until `RunTests.cmd` and the Windows smoke checklist succeed.
