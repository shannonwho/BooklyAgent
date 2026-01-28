# Linear Integration Scripts

Scripts to help integrate System Prompt improvements with Linear issue tracking.

## Setup

### 1. Get Linear API Key

1. Go to Linear Settings → API → Personal API keys
2. Click "Create API key"
3. Copy the key (starts with `lin_api_...`)

### 2. Get Team ID (Optional)

The script can auto-detect your team, but you can also set it manually:

1. Open Linear in your browser
2. Look at the URL: `linear.app/team/{team-id}/...`
3. Copy the team ID

### 3. Set Environment Variables

**Option A: Export in shell**
```bash
export LINEAR_API_KEY="lin_api_your-key-here"
export LINEAR_TEAM_ID="your-team-id"  # Optional
```

**Option B: Create `.env` file** (recommended)
```bash
# In scripts/ directory
LINEAR_API_KEY=lin_api_your-key-here
LINEAR_TEAM_ID=your-team-id
```

**Note**: The script will automatically load `.env` if `python-dotenv` is installed:
```bash
pip install python-dotenv
```

## Usage

### Automated Issue Creation

Run the script to create all issues automatically:

```bash
python scripts/create_linear_issues.py
```

The script will:
1. Create an epic: "System Prompt & Rules Enhancement"
2. Create 10 issues (one for each pattern file)
3. Link all issues to the epic
4. Set priorities based on the plan

### Manual Creation

If you prefer to create issues manually:

1. Read `docs/linear-integration-guide.md` for templates
2. Use Linear's web interface
3. Copy issue descriptions from the script

### Using Linear CLI

```bash
# Install Linear CLI
npm install -g @linear/cli

# Login
linear login

# Create an issue
linear issue create \
  --title "Python/FastAPI Patterns" \
  --description "$(cat issue-template.md)" \
  --team "Engineering" \
  --priority "High"
```

## Issue Structure

The script creates:

**Epic**: System Prompt & Rules Enhancement

**High Priority Issues**:
1. Python/FastAPI Patterns Documentation
2. Database/SQLAlchemy Patterns Documentation
3. API/WebSocket Patterns Documentation
4. Error Handling Patterns Documentation
5. Security Patterns Documentation

**Medium Priority Issues**:
6. Testing Patterns Documentation
7. Observability Patterns Documentation
8. Agent Patterns Documentation

**Low Priority Issues**:
9. Code Organization Patterns Documentation
10. Enhance React Patterns Documentation

## Troubleshooting

### API Key Issues

- Ensure your API key starts with `Bearer ` or the script will add it
- Check that the API key has permission to create issues

### Team ID Issues

- The script will prompt you to select a team if not set
- Make sure you have access to the team

### GraphQL Errors

- Check Linear API status
- Verify your API key permissions
- Check the error message for specific issues

## Next Steps

After creating issues:

1. Review issues in Linear
2. Assign to sprints/cycles
3. Start with Phase 1 (High Priority) issues
4. Link PRs to issues as you implement
5. Update issue status as you progress
