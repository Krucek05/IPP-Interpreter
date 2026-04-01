# Tester CLI Spec Checks

This suite checks whether all three tester templates parse CLI arguments consistently with the
requirements in the `Spouštění nástroje` section at the end of [`ipp26.tex`](/home/ondryaso/Projects/02_IPP/ipp26/ipp26.tex).

Checked areas:
- exactly one positional `tests_dir` argument
- support for `-h/--help`, `-r/--recursive`, `-o/--output`, `--dry-run`
- support for include/exclude filters (`-i/-e`, `-ic/-it/-ec/-et`, long forms)
- repeated filter flags
- basic path validation (`tests_dir` exists, output parent exists)
- cross-language consistency of exit codes

## Run

```bash
python3 tests/tester_cli_spec/run_tester_cli_spec.py
```

Run only specific cases:

```bash
python3 tests/tester_cli_spec/run_tester_cli_spec.py --case missing_positional --case filters_short_ok
```

Optional Python interpreter override:

```bash
TESTER_CLI_PYTHON=python/tester/.venv/bin/python \
python3 tests/tester_cli_spec/run_tester_cli_spec.py
```

Note: the runner executes `npm run build` in `typescript/tester` before running cases.
