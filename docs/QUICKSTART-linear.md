# Quick Start: Linear Integration

## TL;DR

1. **Get Linear API Key**: Linear Settings → API → Personal API keys
2. **Run the script**: `python scripts/create_linear_issues.py`
3. **Start working**: Issues are created and linked to an epic

## Three Integration Options

### 🚀 Option 1: Automated Script (Recommended)

**Best for**: Creating all issues at once

```bash
# 1. Set your API key
export LINEAR_API_KEY="lin_api_your-key-here"

# 2. Run the script
python scripts/create_linear_issues.py

# 3. Done! Check Linear for your epic and issues
```

**What it does**:
- Creates epic: "System Prompt & Rules Enhancement"
- Creates 10 issues (one per pattern file)
- Links issues to epic
- Sets priorities automatically

### 📝 Option 2: Linear CLI

**Best for**: Creating issues one at a time

```bash
# Install
npm install -g @linear/cli
linear login

# Create issue
linear issue create \
  --title "Python/FastAPI Patterns" \
  --team "Engineering" \
  --priority "High"
```

### 🖱️ Option 3: Manual Creation

**Best for**: Full control, custom workflows

1. Open Linear
2. Create epic manually
3. Use templates from `docs/linear-integration-guide.md`
4. Create issues one by one

## Recommended Workflow

### Step 1: Create Issues
Use Option 1 (automated script) to create all issues at once.

### Step 2: Organize in Linear
- Assign issues to current sprint/cycle
- Add labels: `documentation`, `backend`, `frontend`
- Set due dates if needed

### Step 3: Start Implementation
Work through issues in priority order:
1. **High Priority** (Phase 1): Python, Database, API, Error Handling, Security
2. **Medium Priority** (Phase 2): Testing, Observability, Agent
3. **Low Priority** (Phase 3): Code Organization, React Enhancement

### Step 4: Link PRs
When creating PRs, reference Linear issues:
```markdown
Fixes LINEAR-123
Implements LINEAR-124
```

Linear will automatically link PRs to issues.

## Issue Structure Created

```
Epic: System Prompt & Rules Enhancement
├── [High] Python/FastAPI Patterns
├── [High] Database/SQLAlchemy Patterns
├── [High] API/WebSocket Patterns
├── [High] Error Handling Patterns
├── [High] Security Patterns
├── [Medium] Testing Patterns
├── [Medium] Observability Patterns
├── [Medium] Agent Patterns
├── [Low] Code Organization Patterns
└── [Low] Enhance React Patterns
```

## Next Steps

1. ✅ Run the script to create issues
2. ✅ Review issues in Linear
3. ✅ Start with Phase 1 (High Priority)
4. ✅ Link PRs as you implement
5. ✅ Update issue status as you progress

## Need Help?

- **Full guide**: See `docs/linear-integration-guide.md`
- **Script help**: See `scripts/README.md`
- **Issue templates**: See `docs/linear-integration-guide.md`
