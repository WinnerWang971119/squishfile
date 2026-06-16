# PDF Discard Larger Output Plan

**Goal:** Prevent PDF compression from replacing a file with output that is not smaller than the original.

**Approach:** Add a PDF-level final-size guard after the PDF is rewritten. If the rewritten PDF is greater than or equal to the original size, return the original bytes with `skipped: true` and an explanatory message.

## Scope

- **In scope:**
  - Add a regression test for an image-backed PDF whose rewritten output is not smaller.
  - Add the final-size guard in `compress_pdf`.
- **Out of scope:**
  - Aggressive image downscaling.
  - Frontend UI changes.
  - General engine-level guards for non-PDF formats.

## Acceptance Criteria

- [ ] PDF compression returns the original bytes when the rewritten PDF is not smaller.
- [ ] The returned result marks the operation as skipped.
- [ ] Existing PDF compression tests still pass.

## Testing Strategy

| ID | Test Case | Type | Expected Behavior |
|----|-----------|------|-------------------|
| TC1 | PDF rewrite is not smaller than original | Unit | Returns original bytes, original size, and `skipped: true` |
| TC2 | Existing image-heavy PDF compression | Unit | Still produces a valid smaller PDF |

**Run command:** `pytest tests/test_pdf_compressor.py -q`

## Tasks

| ID | Task | Blocked By | Risk | Files | Description |
|----|------|------------|------|-------|-------------|
| T1 | Add regression test | - | low | `tests/test_pdf_compressor.py` | Add TC1. Satisfies AC 1 and AC 2. |
| T2 | Add PDF final-size guard | T1 | low | `squishfile/compressor/pdf.py` | Return original data with `skipped: true` when rewritten PDF size is greater than or equal to original. Satisfies AC 1 and AC 2. |
| T3 | Verify PDF tests | T2 | low | `tests/test_pdf_compressor.py`, `squishfile/compressor/pdf.py` | Run targeted PDF tests. Satisfies AC 3. |

## Notes for Implementer

- Keep the guard in the PDF compressor so this change is scoped only to PDFs.
- Preserve original bytes on skip so downloads cannot grow.
