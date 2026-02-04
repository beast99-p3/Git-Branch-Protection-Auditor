# Visual Quick Start Guide

## 🎯 30-Second Overview

```
YOU → Edit .env → Run Script → Get CSV Report → Fix Issues
      (2 minutes)  (5 minutes)  (Open in Excel)  (Remediate)
```

---

## 📝 **Step 1: Get Your GitHub Token** (2 minutes)

### Go to: https://github.com/settings/tokens

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Settings > Developer Settings                   │
│                                                          │
│  Personal Access Tokens                                 │
│  ┌──────────────────────────────────────────┐          │
│  │ [Generate new token ▼]                   │          │
│  │                                           │          │
│  │ Token (classic)                           │          │
│  └──────────────────────────────────────────┘          │
│                                                          │
│  Note: SOC 2 Compliance Auditor                         │
│                                                          │
│  Scopes:                                                 │
│  ☑ repo         (Full repository access)               │
│  ☑ read:org     (Read organization data)               │
│                                                          │
│  [Generate token]                                        │
└─────────────────────────────────────────────────────────┘

Result: ghp_abc123def456ghi789jkl...
        ↑ Copy this!
```

---

## 📋 **Step 2: Edit Your .env File** (1 minute)

### Open: `.env` in the project folder

**BEFORE (template):**
```bash
GITHUB_ORG=your-org-name
GITHUB_TOKEN=ghp_yourtoken...
CREATE_ISSUES=false
```

**AFTER (your actual values):**
```bash
GITHUB_ORG=acme-corp
GITHUB_TOKEN=ghp_abc123def456ghi789jkl...
CREATE_ISSUES=false
```

**Important:**
- ✅ Use your **organization name** (not your username!)
- ✅ Paste the full token (starts with `ghp_`)
- ✅ Keep `CREATE_ISSUES=false` for first run

---

## ▶️ **Step 3: Run the Auditor** (5-10 minutes)

### Option A: Double-Click Method (Easiest)

```
File Explorer → Navigate to project folder → Double-click:

   📄 run_auditor.bat
```

**You'll see:**
```
================================================
  GitHub SOC 2 Branch Protection Auditor
================================================

Starting SOC 2 Branch Protection Audit for Org: acme-corp
Fetched page 1 (100 repos)...
Fetched page 2 (42 repos)...
Found 142 active repositories. Scanning rules...

Auditing: frontend-app...
Auditing: backend-api...
Auditing: data-pipeline...
...
(continues for each repo)
...

--- Audit Complete ---
Scanned: 142 repositories
✅ Compliant: 120
❌ Non-Compliant: 22
Report saved to: github_audit_report_20260203_143052.csv
```

---

### Option B: Command Line Method (More Control)

**Open Command Prompt or PowerShell:**

```powershell
# Navigate to project
cd "C:\Users\priye\OneDrive - The George Washington University\Documents\Projects\Git Branch Protection Auditor"

# Activate virtual environment
.venv\Scripts\activate

# (Optional) Validate setup first
python validate_setup.py

# Run the auditor
python github_auditor.py
```

**Validation output:**
```
================================================
  Setup Validator
================================================

🔍 Checking environment variables...
  ✅ GITHUB_ORG: acme-corp
  ✅ GITHUB_TOKEN: ghp_abc123...

📚 Checking Python dependencies...
  ✅ requests: 2.31.0
  ✅ pandas: 2.0.3

🔑 Validating GitHub token permissions...
  ✅ Token valid for user: john-doe
  📋 Token scopes: repo, read:org

🏢 Validating organization access...
  ✅ Organization found: Acme Corporation
  ✅ Can access repositories (100 fetched as sample)

================================================
  ✅ All checks passed! Ready to run.
================================================
```

---

## 📊 **Step 4: Review the Report** (Open in Excel)

### Find the file: `github_audit_report_20260203_143052.csv`

**What you'll see:**

```
┌──────────────────────────────────────────────────────────────────────┐
│ Excel / Google Sheets                                                │
├────────────────┬───────────────┬─────────────┬─────────────┬─────────┤
│ repo_name      │ SOC2_COMPLIANT│ pull_request│ approving_  │ status_ │
│                │               │ _before_    │ review_count│ checks  │
│                │               │ merging     │             │         │
├────────────────┼───────────────┼─────────────┼─────────────┼─────────┤
│ frontend-app   │ TRUE          │ TRUE        │ TRUE        │ TRUE    │
│ backend-api    │ TRUE          │ TRUE        │ TRUE        │ FALSE   │
│ data-pipeline  │ FALSE         │ FALSE       │ FALSE       │ FALSE   │  ← Problem!
│ mobile-ios     │ TRUE          │ TRUE        │ TRUE        │ TRUE    │
│ legacy-system  │ FALSE         │ TRUE        │ FALSE       │ FALSE   │  ← Problem!
│ ...            │ ...           │ ...         │ ...         │ ...     │
└────────────────┴───────────────┴─────────────┴─────────────┴─────────┘

Filter SOC2_COMPLIANT = FALSE to see issues ↑
```

### **In Excel:**

1. Click on `SOC2_COMPLIANT` column header
2. Click the filter dropdown ▼
3. Uncheck "TRUE"
4. Click OK

**Result:** Only non-compliant repositories shown!

---

## 🔧 **Step 5: Fix Non-Compliant Repositories**

### For each non-compliant repo, you need to:

```
┌─────────────────────────────────────────────────────────────┐
│  Repository Settings                                         │
│                                                              │
│  1. Go to: https://github.com/acme-corp/repo-name/settings  │
│                                                              │
│  2. Click: "Branches" (left sidebar)                        │
│                                                              │
│  3. Click: "Add branch protection rule"                     │
│     OR                                                       │
│     Click: "Rulesets" → "New ruleset"  (2026 recommended!)  │
│                                                              │
│  4. Configure:                                              │
│     ☑ Require pull request before merging                   │
│     ☑ Require approvals (at least 1)                        │
│     ☑ Require status checks to pass (if you have CI/CD)     │
│     ☑ Require signed commits (recommended)                  │
│     ☑ Require linear history (optional)                     │
│                                                              │
│  5. Click: "Create" or "Save changes"                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 **Step 6: Automatic Issue Creation (Optional)**

### Want to notify repo owners automatically?

**Edit `.env` file:**
```bash
CREATE_ISSUES=true  # Change from false to true
```

**Run the extended script:**
```bash
python github_auditor_with_issues.py
```

**What happens:**
```
For each non-compliant repo:

┌─────────────────────────────────────────────────────────────┐
│  GitHub Issue Created: #123                                  │
│                                                              │
│  Title: 🔒 SOC 2 Compliance: Branch Protection Required     │
│                                                              │
│  Body:                                                       │
│  ⚠️ This repository's default branch does not meet SOC 2    │
│  compliance requirements.                                    │
│                                                              │
│  Missing Controls:                                          │
│  - ❌ pull_request_before_merging                           │
│  - ❌ required_approving_review_count                       │
│                                                              │
│  Required Actions:                                          │
│  1. Enable Pull Request Requirements                        │
│  2. Require Code Reviews (at least 1 reviewer)              │
│  ...                                                         │
│                                                              │
│  Labels: 🏷️ security, compliance, soc2, branch-protection  │
└─────────────────────────────────────────────────────────────┘

Repository owners get notified automatically! 📧
```

---

## 📅 **Regular Audits**

### Schedule monthly audits:

**Windows Task Scheduler:**
```
1. Open: Task Scheduler
2. Create Basic Task
3. Name: "GitHub SOC 2 Audit"
4. Trigger: Monthly (first Monday)
5. Action: Start a program
   Program: C:\Users\priye\OneDrive - ...\run_auditor.bat
6. Finish
```

**Or just set a reminder:**
- Run auditor on first Monday of each month
- Track compliance trends over time
- Share results with security team

---

## 🎓 **Understanding Results**

### What "SOC 2 Compliant" Means:

```
✅ SOC2_COMPLIANT = TRUE
   → Pull requests are REQUIRED
   → Code reviews are REQUIRED (at least 1 approver)
   → No one can push directly to main/master
   → Two-person rule enforced

❌ SOC2_COMPLIANT = FALSE
   → Either pull requests OR code reviews are missing
   → Direct pushes to main/master are allowed
   → Fails the "separation of duties" requirement
```

### SOC 2 Control Mapping:

| Control | Requirement | GitHub Setting |
|---------|-------------|----------------|
| **CC6.1** | Change Management | Pull requests required |
| **CC2.2** | Internal Oversight | Approving reviews ≥ 1 |
| **CC7.1** | System Operations | Status checks pass |
| **CC6.8** | Data Integrity | Signed commits |

---

## 💡 **Pro Tips**

### 1. Test on a Small Org First
If you have access to multiple orgs, test with a smaller one (5-10 repos)

### 2. Review with Your Team
Share the CSV with DevOps/Security team before enabling auto-issues

### 3. Gradual Rollout
- Week 1: Run audit, identify gaps
- Week 2: Share findings with teams
- Week 3: Enable auto-issue creation
- Week 4: Track remediation progress

### 4. Export to Excel Pivot Table
```
Excel → Insert → PivotTable
Rows: visibility (public/private)
Values: Count of SOC2_COMPLIANT

See compliance by repo visibility!
```

---

## 🆘 **Quick Troubleshooting**

| Error | Fix |
|-------|-----|
| "Module not found" | Run: `.venv\Scripts\activate` then `pip install -r requirements.txt` |
| "401 Unauthorized" | Regenerate your GitHub token with correct scopes |
| "404 Not Found" | Check org name spelling (use org name, not username) |
| "No repos found" | Verify token has `read:org` permission |
| "Rate limit" | Wait 1 hour or increase `time.sleep()` in script |

---

## ✅ **Success Checklist**

Before running, verify:

- [ ] `.env` file is configured with real values
- [ ] GitHub token has `repo` and `read:org` scopes
- [ ] Virtual environment is activated
- [ ] You're in the correct directory
- [ ] `validate_setup.py` passes all checks

---

**You're ready to audit! 🚀**

For detailed explanations, see:
- [HOW_TO_RUN.md](HOW_TO_RUN.md) - Complete guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - How it works
- [README.md](README.md) - Full documentation
