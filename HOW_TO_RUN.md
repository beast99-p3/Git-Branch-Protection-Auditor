# 🚀 How to Run This Project - Complete Guide

## 📋 **What You Need to Change**

### 1. **Edit the `.env` file** (REQUIRED)

Open [.env](.env) and update these two values:

```bash
# YOUR GitHub organization name (e.g., "microsoft", "google", "my-company")
GITHUB_ORG=your-org-name

# YOUR Personal Access Token from https://github.com/settings/tokens
GITHUB_TOKEN=ghp_yourtoken123456789...

# Leave as false for your first run
CREATE_ISSUES=false
```

**Where to get your token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Check these permissions:
   - ✅ `repo` (Full repository access)
   - ✅ `read:org` (Read organization data)
4. Generate and copy the token (starts with `ghp_`)

---

## 🎯 **Three Ways to Run**

### **Option 1: Quick Run (Easiest for Windows)**

Just double-click or run:
```bash
run_auditor.bat
```

This automatically:
- Loads your `.env` file
- Activates the virtual environment
- Runs the basic auditor
- Shows you the results

**Want to create issues in non-compliant repos?**
```bash
run_auditor.bat issues
```

---

### **Option 2: Manual Run (More Control)**

**Step 1: Activate virtual environment**
```bash
.venv\Scripts\activate
```

**Step 2: Validate your setup (recommended first time)**
```bash
python validate_setup.py
```

This checks:
- ✅ Your `.env` is configured correctly
- ✅ Your GitHub token works
- ✅ You can access the organization
- ✅ All Python packages are installed

**Step 3a: Run basic auditor (CSV report only)**
```bash
python github_auditor.py
```

**Step 3b: Run extended auditor (creates GitHub issues)**
```bash
python github_auditor_with_issues.py
```

---

### **Option 3: Direct Python Execution**

If you want to skip the virtual environment:
```bash
python -m pip install requests pandas
python github_auditor.py
```

---

## 📊 **What Happens When You Run It**

### **Phase 1: Discovery (30 seconds - 2 minutes)**
```
Starting SOC 2 Branch Protection Audit for Org: acme-corp
Fetched page 1 (100 repos)...
Fetched page 2 (100 repos)...
Fetched page 3 (42 repos)...
Found 242 active repositories. Scanning rules...
```

The script:
1. Connects to GitHub using your token
2. Fetches ALL repositories in your organization (excluding archived/disabled)
3. Uses pagination (100 repos at a time)

---

### **Phase 2: Analysis (2-5 minutes for 100 repos)**
```
Auditing: frontend-web-app...
Auditing: backend-api-service...
Auditing: data-processing-pipeline...
Auditing: mobile-ios-app...
...
```

For each repository:
1. Queries the **Branch Rules API** for the default branch
2. Checks for these SOC 2 controls:
   - ✅ Pull requests required?
   - ✅ Code reviews required?
   - ✅ CI/CD status checks?
   - ✅ Signed commits?
   - ✅ Linear history?
3. Determines if repo passes SOC 2 compliance
4. (Optional) Creates a GitHub issue if non-compliant

**Rate limiting:** 0.3 second delay between repos to be respectful

---

### **Phase 3: Results**
```
=============================================================
--- Audit Complete ---
=============================================================
Scanned: 242 repositories
✅ Compliant: 215
❌ Non-Compliant: 27

📄 Report saved to: github_audit_report_20260203_143052.csv
=============================================================
```

---

## 📄 **Understanding the Output**

### **CSV Report File**
Location: `github_audit_report_YYYYMMDD_HHMMSS.csv`

**Open with:** Excel, Google Sheets, or any spreadsheet app

**Key Columns:**

| Column | Meaning | Values |
|--------|---------|--------|
| `repo_name` | Repository name | `frontend-app` |
| `SOC2_COMPLIANT` | Overall pass/fail | `TRUE` or `FALSE` |
| `pull_request_before_merging` | PRs required to merge? | `TRUE` or `FALSE` |
| `required_approving_review_count` | Code reviews required? | `TRUE` or `FALSE` |
| `required_status_checks` | CI/CD checks enforced? | `TRUE` or `FALSE` |
| `required_signatures` | Commits must be signed? | `TRUE` or `FALSE` |
| `non_fast_forward` | Linear history enforced? | `TRUE` or `FALSE` |
| `visibility` | Repo visibility | `public`, `private`, `internal` |
| `issue_created` | Was issue created? | `TRUE` or `FALSE` |
| `issue_number` | GitHub issue number | `123` (or blank) |

**How to use it:**
1. Open in Excel
2. Filter `SOC2_COMPLIANT` = `FALSE` to see non-compliant repos
3. Share with your team for remediation

---

## 🔧 **Where to Run This**

### **Working Directory**
```
C:\Users\priye\OneDrive - The George Washington University\Documents\Projects\Git Branch Protection Auditor
```

**All commands must be run from this directory!**

To navigate there:
```bash
cd "C:\Users\priye\OneDrive - The George Washington University\Documents\Projects\Git Branch Protection Auditor"
```

### **File Structure**
```
Git Branch Protection Auditor/
├── .env                          ← EDIT THIS with your credentials
├── github_auditor.py             ← Basic version
├── github_auditor_with_issues.py ← Extended version
├── validate_setup.py             ← Test your setup
├── run_auditor.bat               ← Windows quick-run
├── requirements.txt              ← Python packages
└── github_audit_report_*.csv     ← Generated reports (created after run)
```

---

## ⚠️ **Common Issues & Solutions**

### ❌ "Please set GITHUB_ORG and GITHUB_TOKEN"
**Problem:** `.env` file not configured

**Solution:** 
1. Open [.env](.env)
2. Replace `your-org-name` with your actual GitHub org
3. Replace `ghp_yourtoken...` with your actual token

---

### ❌ "401 Unauthorized"
**Problem:** GitHub token is invalid or expired

**Solution:**
1. Generate a new token at https://github.com/settings/tokens
2. Make sure you selected `repo` and `read:org` permissions
3. Update [.env](.env) with the new token

---

### ❌ "404 Not Found" (organization)
**Problem:** Wrong organization name or no access

**Solution:**
1. Verify your org name at https://github.com/orgs/YOUR-ORG
2. Make sure you're a member of the organization
3. Check that your token has `read:org` permission

---

### ❌ "ModuleNotFoundError: No module named 'requests'"
**Problem:** Python packages not installed

**Solution:**
```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### ❌ No repositories found
**Problem:** Token doesn't have organization access

**Solution:**
1. Make sure you're using your **organization name**, not your username
2. Verify you're a member of the organization
3. Check token has `read:org` scope

---

## 🎯 **Recommended First Run**

**For your first time, follow this exact sequence:**

```bash
# 1. Navigate to project directory
cd "C:\Users\priye\OneDrive - The George Washington University\Documents\Projects\Git Branch Protection Auditor"

# 2. Edit .env file
notepad .env

# 3. Activate virtual environment
.venv\Scripts\activate

# 4. Validate setup
python validate_setup.py

# 5. Run basic auditor (if validation passed)
python github_auditor.py

# 6. Review the CSV report
# Open github_audit_report_*.csv in Excel
```

---

## 🚀 **Next Steps After First Run**

### **Review Non-Compliant Repositories**
1. Open the CSV in Excel
2. Filter `SOC2_COMPLIANT = FALSE`
3. Share the list with repository owners

### **Enable Automatic Issue Creation**
1. Edit [.env](.env)
2. Change `CREATE_ISSUES=false` to `CREATE_ISSUES=true`
3. Run: `python github_auditor_with_issues.py`
4. Issues will be created with label `soc2` in each non-compliant repo

### **Schedule Regular Audits**
Run this monthly or quarterly to track compliance over time:
```bash
# Windows Task Scheduler
run_auditor.bat
```

---

## 📚 **Additional Documentation**

- [QUICKSTART.md](QUICKSTART.md) - Windows-specific getting started guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - How the system works internally
- [README.md](README.md) - Full project documentation

---

## 🔐 **Security Reminder**

- ✅ `.env` is in `.gitignore` - your token is safe
- ✅ Never commit `.env` to git
- ✅ Rotate your GitHub token every 90 days
- ✅ Use a dedicated "audit" token with minimal permissions

---

**Questions?** Check [README.md](README.md) or [ARCHITECTURE.md](ARCHITECTURE.md) for more details!
