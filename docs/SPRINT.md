# Sprint Plan: Agent-First CLI

This CLI is designed primarily for AI agent consumption. Priorities are set accordingly.

## High Priority (v1 Release)

### Safety & Security
| Issue | Title | Why |
|-------|-------|-----|
| [#11](https://github.com/theFong/mmoney-cli/issues/11) | Read-only safe mode | **Critical** - Agents must not mutate financial data |
| [#16](https://github.com/theFong/mmoney-cli/issues/16) | Store session in system keychain | Secure credential storage, important for agents |

### Agent-Friendly Output
| Issue | Title | Why |
|-------|-------|-----|
| [#10](https://github.com/theFong/mmoney-cli/issues/10) | Agent-friendly output formats | CSV, JSONL, plain text - simpler than nested JSON |
| [#12](https://github.com/theFong/mmoney-cli/issues/12) | Structured error responses | Agents need parseable errors + consistent exit codes |

### Documentation
| Issue | Title | Why |
|-------|-------|-----|
| [#19](https://github.com/theFong/mmoney-cli/issues/19) | Comprehensive command & object docs | Document every command, field, and Monarch Money concept |
| [#13](https://github.com/theFong/mmoney-cli/issues/13) | Document JSON schema | Machine-readable schema for agent integration |

### Code Quality & CI
| Issue | Title | Why |
|-------|-------|-----|
| [#3](https://github.com/theFong/mmoney-cli/issues/3) | CI: Dead code linting | Keep context clean for agents |
| [#4](https://github.com/theFong/mmoney-cli/issues/4) | CI: Lint rules and formatting | Code quality and consistency |
| [#17](https://github.com/theFong/mmoney-cli/issues/17) | Generate realistic mock data | Enable fast iteration and offline testing |

### Distribution
| Issue | Title | Why |
|-------|-------|-----|
| [#1](https://github.com/theFong/mmoney-cli/issues/1) | Publish to PyPI | Distribution (read-only version first) |

## Medium Priority

| Issue | Title | Why |
|-------|-------|-----|
| [#15](https://github.com/theFong/mmoney-cli/issues/15) | Move config to ~/.mmoney | Better usability, single session location |
| [#6](https://github.com/theFong/mmoney-cli/issues/6) | Add type hints | Helps agent tooling, IDE support |
| [#9](https://github.com/theFong/mmoney-cli/issues/9) | Improve error handling | Relates to #12 |

## Low Priority

| Issue | Title | Why |
|-------|-------|-----|
| [#7](https://github.com/theFong/mmoney-cli/issues/7) | Refactor cli.py into modules | Internal, doesn't affect agents |
| [#8](https://github.com/theFong/mmoney-cli/issues/8) | Add logging with --debug flag | Human debugging, less relevant for agents |

## Completed

| Issue | Title |
|-------|-------|
| [#2](https://github.com/theFong/mmoney-cli/issues/2) | ~~CI: Build and test pipeline~~ |
| [#5](https://github.com/theFong/mmoney-cli/issues/5) | ~~Add unit and integration tests~~ |

---

## v1 Release Checklist

### 1. Safety First
- [ ] Remove/gate all mutation commands (#11)
- [ ] Store credentials in system keychain (#16)
- [ ] Document read-only commands clearly

### 2. Agent-Friendly Output
- [ ] Implement `--format csv` for list commands (#10)
- [ ] Implement `--format jsonl` for streaming (#10)
- [ ] Implement `--format text` for simple parsing (#10)
- [ ] Structured JSON error responses (#12)
- [ ] Consistent exit codes (#12)

### 3. Documentation
- [ ] Document all commands with examples (#19)
- [ ] Document all data objects and fields (#19)
- [ ] Reference Monarch Money concepts (#19)
- [ ] JSON schema for all outputs (#13)
- [ ] Error code reference (#12)

### 4. Code Quality
- [ ] Dead code linting in CI (#3)
- [ ] Lint rules enforced (#4)
- [ ] Realistic mock data for tests (#17)

### 5. Distribution
- [ ] Move config to ~/.mmoney (#15)
- [ ] Publish read-only version to PyPI (#1)

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

These commands will be disabled or removed in the initial release:

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
