# SquishFile Startup/Test Fix Plan

**Goal:** Make backend startup and pytest robust when frontend build output is missing or partially present.

**Approach:** Harden backend static serving. `squishfile.main` should only mount built static assets when the required paths exist, so importing the FastAPI app never crashes because of a partial `dist` directory.

## Scope

- **In scope:**
  - Guard `/assets` mounting on `squishfile/frontend/dist/assets` existing.
  - Guard SPA fallback on `squishfile/frontend/dist/index.html` existing.
  - Add a regression test for partial frontend build output.
  - Verify frontend build and pytest.
- **Out of scope:**
  - Changing frontend UI behavior.
  - Changing Vite build output paths.
  - Cleaning generated files or modifying the existing unrelated `frontend/package-lock.json` change.

## Decisions

- Static asset mount is optional: mount only when the built assets directory exists, because development and tests should not require a production frontend build.
- SPA fallback is optional: register it only when `index.html` exists, because missing frontend output should not break API-only usage.
- Existing dirty frontend lockfile remains untouched and uncommitted.

## Acceptance Criteria

- [ ] Importing `squishfile.main` does not crash when `dist/` exists without `assets/`.
- [ ] Backend API routes still work when no production frontend is available.
- [ ] Built frontend is still served when `dist/index.html` and `dist/assets/` exist.
- [ ] `pytest` passes using a workspace temp/cache workaround if Windows temp permissions interfere.
- [ ] `npm run build` still passes.

## Error Handling

- **Partial frontend build output:** Skip missing static mounts instead of raising at import time.
- **No frontend build output:** Keep API routes available and do not register a catch-all SPA route.
- **Built frontend present:** Serve static assets and fall back to `index.html` for non-API paths.

## Testing Strategy

**Levels:** Unit, integration, build.

| ID  | Test Case                         | Type        | Expected Behavior                         |
|-----|-----------------------------------|-------------|-------------------------------------------|
| TC1 | Partial frontend dist without assets | Unit     | App import/setup succeeds                 |
| TC2 | API health endpoint               | Integration | Returns 200 and version                   |
| TC3 | Frontend production build         | Build       | Vite emits `dist/index.html` and assets   |
| TC4 | Full pytest suite                 | Regression  | All tests pass                            |

**Run commands:**

```bash
cd frontend
npm run build
```

```bash
pytest -q --basetemp .tmp\pytest -p no:cacheprovider
```

## Tasks

| ID | Task | Blocked By | Risk | Files | Description |
|----|------|------------|------|-------|-------------|
| T1 | Harden frontend static serving | — | low | `squishfile/main.py` | Check `dist/index.html` and `dist/assets` independently before registering routes. Satisfies AC1, AC2, and AC3. |
| T2 | Add regression coverage | T1 | low | `tests/test_main.py` | Add a test that verifies app setup succeeds when the frontend dist directory exists without an assets directory. Satisfies AC1 and AC2. |
| T3 | Verify commands | T1, T2 | low | none | Run frontend build and pytest commands. Satisfies AC4 and AC5. |

## Notes for Implementer

- Keep the fix minimal; no frontend refactor.
- Avoid touching the existing dirty `frontend/package-lock.json`.
- If Windows temp permissions interfere with pytest, use the workspace-owned basetemp and disable pytest cache as shown above.
