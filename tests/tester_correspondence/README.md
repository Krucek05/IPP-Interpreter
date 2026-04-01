# Tester Correspondence Tests

This suite checks that output models in:
- `python/tester`
- `php/tester`
- `typescript/tester`

serialize to the same JSON.

Each case directory under `cases/` contains three scripts:
- `case.py`
- `case.php`
- `case.mjs`

All three scripts construct the same `TestReport` model and print JSON using that language's
native model serialization path.

## Run

From repository root:

```bash
python3 tests/tester_correspondence/run_tester_correspondence.py
```

The runner builds `typescript/tester` first (`npm run build`) so `dist/models.js` reflects current
TypeScript sources.

Run selected cases only:

```bash
python3 tests/tester_correspondence/run_tester_correspondence.py \
  --case 001_empty_report \
  --case 003_full_results_matrix
```

Use specific Python interpreter for Python tester scripts:

```bash
TESTER_CORR_PYTHON=python/tester/.venv/bin/python \
python3 tests/tester_correspondence/run_tester_correspondence.py
```
