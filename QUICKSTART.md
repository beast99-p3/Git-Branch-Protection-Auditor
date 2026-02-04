# Quick Start Guide - Windows

## Before First Run

### 1. Get Your GitHub Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Set these permissions:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (Read org and team membership)
4. Click **"Generate token"**
5. **Copy the token immediately** (you won't see it again!)

### 2. Configure the `.env` File

Open [.env](.env) and update these values:

```bash
# Replace with YOUR organization name (not your username!)
GITHUB_ORG=acme-corp

# Paste your token here
GITHUB_TOKEN=ghp_abcdef1234567890...

# Leave as false for first run
CREATE_ISSUES=false
```

**Important:** 
- Use your **organization name**, not your personal username
- Keep the `ghp_` prefix in the token
- Don't add quotes around values

---

## Running the Auditor

### Method 1: Quick Run (Easiest) - Windows Batch File

```bash
# Basic audit (CSV report only)
run_auditor.bat

# Extended audit (creates GitHub issues)
run_auditor.bat issues
```

### Method 2: Manual Run (More Control)

**Activate virtual environment first:**
```bash
.venv\Scripts\activate
```

**Then run either script:**

```bash
# Basic auditor - generates CSV report
python github_auditor.py

# Extended auditor - creates issues in non-compliant repos
python github_auditor_with_issues.py
```

---

## What Happens When You Run It?

### Phase 1: Discovery (1-2 minutes)
```
Starting SOC 2 Branch Protection Audit for Org: acme-corp
Fetched page 1 (42 repos)...
Found 42 active repositories. Scanning rules...
```

### Phase 2: Analysis (2-5 minutes for 100 repos)
```
Auditing: frontend-app...
Auditing: backend-api...
Auditing: data-pipeline...
```

### Phase 3: Results
```
=============================================================
--- Audit Complete ---
=============================================================
Scanned: 42 repositories
✅ Compliant: 38
❌ Non-Compliant: 4

📄 Report saved to: github_audit_report_20260203_143052.csv
=============================================================
```

---

## Output Files

### CSV Report (`github_audit_report_YYYYMMDD_HHMMSS.csv`)

Contains columns:
- `repo_name` - Repository name
- `SOC2_COMPLIANT` - TRUE/FALSE overall status
- `pull_request_before_merging` - PRs required?
- `required_approving_review_count` - Code reviews required?
- `required_status_checks` - CI/CD checks active?
- `required_signatures` - Commit signing active?
- `non_fast_forward` - Linear history enforced?
- `visibility` - public/private/internal
- `audit_timestamp` - When audited
- `issue_created` - Was a GitHub issue created? (extended version only)
- `issue_number` - Issue number if created (extended version only)

**Open in Excel or Google Sheets for analysis.**

---

## Troubleshooting

### Error: "Please set GITHUB_ORG and GITHUB_TOKEN"
- Your `.env` file is not configured
- Edit [.env](.env) and add your credentials

### Error: "401 Unauthorized"
- Your GitHub token is invalid or expired
- Generate a new token at https://github.com/settings/tokens

### Error: "404 Not Found" on organization
- You typed the org name wrong
- Or your token doesn't have access to that organization

### No repositories found
- Check if your token has `read:org` permission
- Verify you're using the organization name, not your username

### Rate limiting (429 errors)
- Increase the `time.sleep(0.3)` value in the script
- Or wait and run again later

---

## Next Steps

### First Run: Basic Audit
1. Run `run_auditor.bat` (without arguments)
2. Review the CSV to see which repos are non-compliant
3. Share with your team for review

### Second Run: Auto-Remediation
1. Edit [.env](.env) and set `CREATE_ISSUES=true`
2. Run `run_auditor.bat issues`
3. The script will create labeled issues in non-compliant repos
4. Repo owners will see the issues and can remediate

---

## Security Notes

- **Never commit `.env` to git** (already in .gitignore)
- Rotate your token every 90 days
- Use a dedicated "audit" token with minimal permissions
- For production use, consider GitHub Apps instead of PATs

---

**Questions?** Check [README.md](README.md) for full documentation.
