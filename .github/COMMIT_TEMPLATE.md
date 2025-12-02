# Commit Message Template

## Format

```
<type>: <short description>

<detailed description if needed>
```

## Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code change that neither fixes nor adds
- `chore:` - Maintenance tasks
- `test:` - Adding or fixing tests

## Pre-Commit Checklist

Before committing, verify:

- [ ] Code tested and working
- [ ] CLAUDE.md reflects current state (if architecture changed)
- [ ] README.md accurate (if features changed)
- [ ] docs/CHANGELOG.md updated (if significant change)
- [ ] No references to deleted files
- [ ] No temporary/debug code

## Examples

```
feat: Add sector comparison chart to dashboard

fix: Resolve UnboundLocalError in batch processing

docs: Update installation instructions for Python 3.12

chore: Remove legacy dashboard files
```
