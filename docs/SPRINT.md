# Sprint Plan: Agent-First CLI

This CLI is designed primarily for AI agent consumption. Priorities are set accordingly.

## High Priority (v1 Release)

| Issue | Title | Why |
|-------|-------|-----|
| [#11](https://github.com/theFong/mmoney-cli/issues/11) | Read-only safe mode | **Critical** - Agents must not mutate financial data |
| [#12](https://github.com/theFong/mmoney-cli/issues/12) | Structured error responses | Agents need parseable errors + consistent exit codes |
| [#10](https://github.com/theFong/mmoney-cli/issues/10) | Agent-friendly output formats | CSV, JSONL, plain text - simpler than nested JSON |
| [#13](https://github.com/theFong/mmoney-cli/issues/13) | Document JSON schema | Agents need to know output structure |
| [#1](https://github.com/theFong/mmoney-cli/issues/1) | Publish to PyPI | Distribution |
| [#2](https://github.com/theFong/mmoney-cli/issues/2) | CI: Build and test pipeline | Reliability |
| [#5](https://github.com/theFong/mmoney-cli/issues/5) | Add unit and integration tests | Reliability |

## Medium Priority

| Issue | Title | Why |
|-------|-------|-----|
| [#3](https://github.com/theFong/mmoney-cli/issues/3) | CI: Dead code linting | Code quality |
| [#4](https://github.com/theFong/mmoney-cli/issues/4) | CI: Lint rules and formatting | Code quality |
| [#6](https://github.com/theFong/mmoney-cli/issues/6) | Add type hints | Helps agent tooling, IDE support |
| [#9](https://github.com/theFong/mmoney-cli/issues/9) | Improve error handling | Relates to #12 |

## Low Priority

| Issue | Title | Why |
|-------|-------|-----|
| [#7](https://github.com/theFong/mmoney-cli/issues/7) | Refactor cli.py into modules | Internal, doesn't affect agents |
| [#8](https://github.com/theFong/mmoney-cli/issues/8) | Add logging with --debug flag | Human debugging, less relevant for agents |

## v1 Release Checklist

1. **Safety First**
   - [ ] Remove/gate all mutation commands (#11)
   - [ ] Document read-only commands clearly

2. **Agent-Friendly Output**
   - [ ] Implement `--format csv` for list commands (#10)
   - [ ] Implement `--format jsonl` for streaming (#10)
   - [ ] Implement `--format text` for simple parsing (#10)
   - [ ] Structured JSON error responses (#12)
   - [ ] Consistent exit codes (#12)

3. **Documentation**
   - [ ] JSON schema for all command outputs (#13)
   - [ ] Error code reference (#12)
   - [ ] Agent usage examples in README

4. **Quality & Distribution**
   - [ ] CI pipeline running (#2)
   - [ ] Core tests passing (#5)
   - [ ] Publish read-only version to PyPI (#1)

## Output Formats for Agents

| Format | Flag | Best For |
|--------|------|----------|
| JSON | `--format json` (default) | Complex nested data, backwards compat |
| CSV | `--format csv` | Tabular data (transactions, accounts) |
| JSONL | `--format jsonl` | Streaming, line-by-line processing |
| Plain | `--format text` | Simple extraction, grep/awk |

## Mutation Commands (Gated in v1)

These commands will be disabled or removed in the initial release:

- `accounts create` / `update` / `delete`
- `transactions create` / `update` / `delete` / `split`
- `categories create`
- `tags create`

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
