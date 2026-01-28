# Linear Integration Guide for System Prompt Improvements

## Overview

This guide provides multiple approaches to track the System Prompt & Rules Enhancement work in Linear, from manual creation to automated scripts.

## Integration Options

### Option 1: Linear API (Recommended for Automation)

**Best for**: Creating multiple issues programmatically, batch operations

**Requirements**:
- Linear API key (Settings → API → Personal API keys)
- Team ID (found in Linear URL: `linear.app/team/{team-id}/...`)
- Python 3.8+ with `requests` library

**Setup**:
```bash
pip install requests python-dotenv
```

**API Endpoint**: `https://api.linear.app/graphql`

### Option 2: Linear CLI

**Best for**: Quick issue creation from terminal

**Installation**:
```bash
npm install -g @linear/cli
linear login
```

**Usage**:
```bash
linear issue create --title "Python/FastAPI Patterns" --description "..." --team "Engineering"
```

### Option 3: Manual Creation (Simplest)

**Best for**: One-off issues, when you want full control

**Steps**:
1. Open Linear
2. Create Epic: "System Prompt & Rules Enhancement"
3. Create issues under the epic
4. Use the issue templates provided below

## Recommended Issue Structure

### Epic: System Prompt & Rules Enhancement

**Description**:
```
Enhance Cursor rules system by adding comprehensive backend patterns and improving existing frontend patterns. This will provide consistent guidance for both frontend and backend development in the BooklyAgent codebase.

**Goals**:
- Document Python/FastAPI patterns
- Establish database/SQLAlchemy conventions
- Standardize error handling
- Add testing, security, and observability patterns
- Improve agent-specific patterns

**Success Criteria**:
- All backend code patterns documented
- Rules consistent with codebase
- Rules actionable with examples
- Rules complement existing React patterns
```

### Issue Template

**Title**: `[Pattern Type] Patterns Documentation`

**Description Template**:
```markdown
## Overview
Create comprehensive pattern documentation for [pattern type] in `.cursor/rules/[filename].mdc`

## Scope
- [ ] Pattern 1
- [ ] Pattern 2
- [ ] Pattern 3

## File Location
`.cursor/rules/[filename].mdc`

## Key Patterns to Document
1. Pattern name
   - Description
   - Example from codebase
   - Best practices

## Reference Files
- `backend/[relevant-file].py`
- `docs/[relevant-doc].md`

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] All patterns documented with examples
- [ ] Consistent with existing `react-patterns.mdc` format
- [ ] Includes code examples from codebase
- [ ] Cross-references related patterns
```

## Priority Breakdown

### High Priority (Phase 1)
1. **Python/FastAPI Patterns** → `python-patterns.mdc`
2. **Database/SQLAlchemy Patterns** → `database-patterns.mdc`
3. **API/WebSocket Patterns** → `api-patterns.mdc`
4. **Error Handling Patterns** → `error-handling.mdc`
5. **Security Patterns** → `security-patterns.mdc`

### Medium Priority (Phase 2)
6. **Testing Patterns** → `testing-patterns.mdc`
7. **Observability Patterns** → `observability-patterns.mdc`
8. **Agent Patterns** → `agent-patterns.mdc`

### Low Priority (Phase 3)
9. **Code Organization** → `code-organization.mdc`
10. **React Patterns Enhancement** → Update `react-patterns.mdc`

## Workflow Recommendations

### 1. Create Epic First
- Title: "System Prompt & Rules Enhancement"
- Team: Your development team
- Priority: High
- Status: In Progress

### 2. Create Issues in Batches
- Create all Phase 1 issues first
- Assign to current sprint/cycle
- Link related issues

### 3. Track Progress
- Update issue status as you work
- Link PRs to issues (use Linear GitHub integration)
- Add comments with progress updates

### 4. Use Labels/Tags
- `documentation`
- `developer-experience`
- `cursor-rules`
- `backend` / `frontend`

## Linear-GitHub Integration

### Setup
1. Linear Settings → Integrations → GitHub
2. Connect repository
3. Enable "Create Linear issue from PR" (optional)

### Workflow
- Reference Linear issue in PR: `Fixes LINEAR-123`
- Linear will auto-link PR to issue
- Status updates sync automatically

## Next Steps

1. Choose your integration method (API, CLI, or Manual)
2. Create the Epic in Linear
3. Use the provided script or templates to create issues
4. Start with Phase 1 (High Priority) issues
5. Track progress and link PRs as you implement
