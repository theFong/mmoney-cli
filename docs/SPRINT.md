# Sprint Plan: Agent-First CLI

This CLI is designed primarily for AI agent consumption. Priorities are set accordingly.

---

## Effort & Blast Radius Analysis

Understanding effort and file changes helps parallelize work and avoid merge conflicts.

### Effort Key
- **S** = Small (< 1 hour)
- **M** = Medium (1-4 hours)
- **L** = Large (4+ hours)

### Open Issues by Blast Radius

#### Isolated (No conflicts - can run in parallel with anything)

| Issue | Title | Effort | Files Changed |
|-------|-------|--------|---------------|
| [#19](https://github.com/theFong/mmoney-cli/issues/19) | Comprehensive docs | L | `docs/*.md`, `README.md` |
| [#13](https://github.com/theFong/mmoney-cli/issues/13) | JSON schema docs | M | `docs/schemas/`, `README.md` |
| [#17](https://github.com/theFong/mmoney-cli/issues/17) | Mock data for tests | M-L | `tests/fixtures/`, `tests/conftest.py` |
| [#3](https://github.com/theFong/mmoney-cli/issues/3) | Dead code linting | S | `pyproject.toml`, `.github/workflows/ci.yml` |
| [#4](https://github.com/theFong/mmoney-cli/issues/4) | Lint rules | S-M | `pyproject.toml`, `.github/workflows/ci.yml` |
| [#1](https://github.com/theFong/mmoney-cli/issues/1) | Publish to PyPI | S | `pyproject.toml`, `.github/workflows/publish.yml` |
| [#20](https://github.com/theFong/mmoney-cli/issues/20) | Git hooks (lint, test, secrets) | S | `.pre-commit-config.yaml`, `.secrets.baseline`, `pyproject.toml` |

#### Localized (Low conflict risk)

| Issue | Title | Effort | Files Changed |
|-------|-------|--------|---------------|
| [#15](https://github.com/theFong/mmoney-cli/issues/15) | Config to ~/.mmoney | S | `mmoney_cli/cli.py` (session path ~20 lines) |

#### Touches cli.py (Moderate conflict risk - coordinate timing)

| Issue | Title | Effort | Files Changed |
|-------|-------|--------|---------------|
| [#6](https://github.com/theFong/mmoney-cli/issues/6) | Add type hints | M | `mmoney_cli/cli.py` (all functions) |
| [#8](https://github.com/theFong/mmoney-cli/issues/8) | Logging/debug flag | M | `mmoney_cli/cli.py` (scattered) |
| [#9](https://github.com/theFong/mmoney-cli/issues/9) | Error handling | M | `mmoney_cli/cli.py` (error paths) |

#### High Blast Radius (Do last or in isolation)

| Issue | Title | Effort | Files Changed |
|-------|-------|--------|---------------|
| [#7](https://github.com/theFong/mmoney-cli/issues/7) | Refactor into modules | L | `mmoney_cli/cli.py` → split into `mmoney_cli/commands/*.py` |

---

## Recommended Execution Order

To maximize parallelism and minimize merge conflicts:

```
Phase 1 (Parallel - no code changes)
├── #19 Comprehensive docs      [docs only]
├── #13 JSON schema docs        [docs only]
├── #17 Mock test data          [tests only]
├── #3  Dead code linting       [CI only]
├── #4  Lint rules              [CI only]
├── #20 Git hooks               [config only]
└── #1  PyPI setup              [config only]

Phase 2 (Sequential - touches cli.py)
├── #15 Config to ~/.mmoney     [small, localized]
├── #6  Add type hints          [before refactor]
├── #8  Logging                 [after type hints]
└── #9  Error handling          [after type hints]

Phase 3 (Isolation - high conflict)
└── #7  Refactor into modules   [do last]
```

---

## Parallel Work Streams

These can run simultaneously without conflicts:

| Stream | Issues | Owner |
|--------|--------|-------|
| Documentation | #19, #13 | Agent A |
| CI/CD | #3, #4, #20, #1 | Agent B |
| Test Infrastructure | #17 | Agent C |
| CLI Code | #15 → #6 → #8 → #9 → #7 | Agent D (sequential) |

---

## Completed

| Issue | Title |
|-------|-------|
| [#2](https://github.com/theFong/mmoney-cli/issues/2) | ~~CI: Build and test pipeline~~ |
| [#5](https://github.com/theFong/mmoney-cli/issues/5) | ~~Add unit and integration tests~~ |
| [#10](https://github.com/theFong/mmoney-cli/issues/10) | ~~Agent-friendly output formats~~ |
| [#11](https://github.com/theFong/mmoney-cli/issues/11) | ~~Read-only safe mode~~ |
| [#12](https://github.com/theFong/mmoney-cli/issues/12) | ~~Structured error responses~~ |
| [#16](https://github.com/theFong/mmoney-cli/issues/16) | ~~Store session in keychain~~ |

---

## v1 Release Checklist

### 1. Documentation (Parallel)
- [ ] Document all commands with examples (#19)
- [ ] Document all data objects and fields (#19)
- [ ] Reference Monarch Money concepts (#19)
- [ ] JSON schema for all outputs (#13)

### 2. Code Quality (Parallel)
- [ ] Dead code linting in CI (#3)
- [ ] Lint rules enforced (#4)
- [ ] Git hooks for lint, test, secrets (#20)
- [ ] Realistic mock data for tests (#17)

### 3. CLI Improvements (Sequential)
- [ ] Move config to ~/.mmoney (#15)
- [ ] Add type hints (#6)
- [ ] Add logging (#8)
- [ ] Improve error handling (#9)

### 4. Distribution
- [ ] Publish to PyPI (#1)

### 5. Future (After v1)
- [ ] Refactor cli.py into modules (#7)

---

## Output Formats for Agents

| Format | Flag | Best For |
|--------|------|----------|
| JSON | `--format json` (default) | Complex nested data, backwards compat |
| CSV | `--format csv` | Tabular data (transactions, accounts) |
| JSONL | `--format jsonl` | Streaming, line-by-line processing |
| Plain | `--format text` | Simple extraction, grep/awk |

---

## Mutation Commands (Gated in v1)

These commands are disabled by default (use `--allow-mutations` to enable):

- `accounts create` / `update` / `delete`
- `transactions create` / `update` / `delete` / `split`
- `categories create`
- `tags create`

---

## Safe Read-Only Commands (v1)

- `auth login` / `use-token` / `logout`
- `accounts list` / `refresh`
- `holdings list` / `history`
- `transactions list` / `summary`
- `categories list`
- `tags list`
- `budgets list`
- `cashflow summary`
- `recurring list`
- `institutions list`
- `subscription details`

---

## References

- [Monarch Money](https://www.monarchmoney.com)
- [Monarch Money Help](https://help.monarchmoney.com)
