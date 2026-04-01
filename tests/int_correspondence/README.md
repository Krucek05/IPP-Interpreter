# INT Correspondence Tests

This suite verifies that the `int` templates in:
- `python/int`
- `php/int`
- `typescript/int`

load the same SOL-XML input into matching in-memory representations.

## What is compared

For each XML case in `cases/valid/*.xml`, each language-specific adapter:
1. loads/parses the XML via the existing project parsing/model infrastructure,
2. converts the loaded program model to a normalized JSON structure.

The runner then compares JSON outputs (`python` is used as the baseline).

## Run

From repository root:

```bash
python3 tests/int_correspondence/run_int_correspondence.py
```

Optional: run selected case(s):

```bash
python3 tests/int_correspondence/run_int_correspondence.py \
  --case 004_send_with_unsorted_args.xml \
  --case 010_deep_nesting.xml
```

Optional: force specific Python interpreter for the Python adapter:

```bash
INT_CORR_PYTHON=python/int/.venv/bin/python \
python3 tests/int_correspondence/run_int_correspondence.py
```
