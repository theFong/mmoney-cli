# Installing the mmoney Claude Skill

## Quick Install

### Option 1: Symlink (Recommended)
```bash
# Create commands directory if it doesn't exist
mkdir -p ~/.claude/commands

# Symlink the skill (updates automatically with repo)
ln -s /path/to/mmoney-cli/docs/claude-skill/mmoney.md ~/.claude/commands/mmoney.md
```

### Option 2: Copy
```bash
# Create commands directory if it doesn't exist
mkdir -p ~/.claude/commands

# Copy the skill file
cp /path/to/mmoney-cli/docs/claude-skill/mmoney.md ~/.claude/commands/mmoney.md
```

### Option 3: Download directly
```bash
mkdir -p ~/.claude/commands
curl -o ~/.claude/commands/mmoney.md https://raw.githubusercontent.com/theFong/mmoney-cli/main/docs/claude-skill/mmoney.md
```

## Prerequisites

1. **Install mmoney CLI**
   ```bash
   pip install mmoney-cli
   # or
   uv pip install mmoney-cli
   ```

2. **Authenticate**
   ```bash
   mmoney auth login
   # or with token
   mmoney auth use-token YOUR_TOKEN
   ```

3. **Verify installation**
   ```bash
   mmoney accounts list
   ```

## Usage

Once installed, you can use natural language in Claude Code:

```
"Show my account balances"
"What did I spend on restaurants last month?"
"How much have I saved this year?"
"Show my investment holdings"
```

## Updating

If you used symlink (Option 1), just pull the latest repo:
```bash
cd /path/to/mmoney-cli && git pull
```

If you copied the file, re-run the copy command.
