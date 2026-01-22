# Security

This document describes how mmoney-cli handles credentials and sensitive data, with special attention to AI agent safety.

## Credential Storage

mmoney-cli stores your session token using your operating system's native credential manager:

| OS | Storage Backend |
|----|-----------------|
| macOS | Keychain |
| Windows | Credential Manager |
| Linux | Secret Service (libsecret/GNOME Keyring) |

**Fallback**: If the system keychain is unavailable, tokens are stored in `~/.mmoney/session.pickle` with restricted file permissions (`600` - owner read/write only).

### Verify Your Storage

```bash
mmoney auth status
# Output: "Authenticated (keychain)" or "Authenticated (file: ~/.mmoney/session.pickle)"
```

## AI Agent Safety

When using mmoney-cli with AI agents like Claude Code:

| Concern | Protection |
|---------|------------|
| **Token visibility** | Stored in OS keychain - agents cannot read keychain contents |
| **Password exposure** | Use interactive login - passwords never in command args |
| **API responses** | Contain only financial data - no credentials returned |
| **Session files** | Restricted permissions (600) - not readable by other users |
| **Shell history** | Avoid `--password` flag - use interactive or `--token` with stdin |

### Why Keychain Storage Matters

AI agents like Claude Code can:
- Execute shell commands
- Read files you grant access to
- See command output

AI agents **cannot**:
- Access OS keychain (requires user authentication)
- See passwords entered interactively
- Read files with restricted permissions (600)

This is why mmoney-cli defaults to keychain storage - your Monarch Money credentials remain invisible to any AI agent or process running on your system.

## Authentication Methods

Listed from most to least secure:

### 1. Interactive Login (Recommended)
```bash
mmoney auth login
# Prompts for email/password - never visible in history or process list
```

### 2. MFA Secret (Best for Automation)
```bash
mmoney auth login -e you@email.com -p "$PASSWORD" --mfa-secret "$MFA_SECRET" --no-interactive
```
- Store MFA secret in environment variable or secrets manager
- Enables automatic session renewal
- Token stored in keychain

### 3. Token from Environment
```bash
export MM_TOKEN="your-token"
mmoney auth login --token "$MM_TOKEN"
```
- Token not visible in shell history
- Useful for CI/CD with secrets management

### 4. Device UUID (Browser Session)
```bash
mmoney auth login -e you@email.com -p "$PASSWORD" --device-uuid "$UUID" --no-interactive
```
- Get UUID from browser: `localStorage.getItem('monarchDeviceUUID')`
- Useful with `claude --chrome` for browser-assisted auth

## What to Avoid

| Practice | Risk | Alternative |
|----------|------|-------------|
| `--password 'mypass'` | Visible in shell history, `ps aux` | Interactive login or env var |
| Committing `.mmoney/` | Token in git history | Add to `.gitignore` |
| Sharing session.pickle | Token compromise | Each user authenticates separately |
| `chmod 777` on session file | Any process can read | Use default permissions (600) |

## Network Security

- All API communication uses HTTPS (TLS 1.2+)
- Tokens sent only in Authorization headers
- No credentials logged in requests or responses
- Session tokens are JWT with expiration

## Data Exposure

Commands return financial data that may include:
- Account names and balances
- Transaction details (merchants, amounts, dates)
- Investment holdings

**No commands return:**
- Passwords or tokens
- Full account numbers
- SSN or sensitive PII

## File Permissions

| File | Permissions | Purpose |
|------|-------------|---------|
| `~/.mmoney/` | 700 | Config directory |
| `~/.mmoney/session.pickle` | 600 | Fallback token storage |

## For SSO Users

If you use Google/Apple SSO to sign into Monarch Money:
1. Go to Monarch Money settings
2. Enable a password for your account
3. Use email + password with mmoney-cli

SSO flows require browser interaction which CLI cannot provide.

## Reporting Security Issues

If you discover a security vulnerability:
1. **Do not** open a public GitHub issue
2. Email: [Create a security advisory on GitHub](https://github.com/theFong/mmoney-cli/security/advisories/new)

We take security seriously and will respond promptly.
