# GitHub Branch Protection Auditor (SOC 2 Compliance)

A Python-based auditor designed for **January 2026 and beyond**, leveraging GitHub's modern **Repository Rulesets API** to audit branch protection compliance across entire organizations for SOC 2 certification.

## 📚 **Documentation Index**

**New to this project? Start here:**
- 🚀 **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)** - 30-second quick start with screenshots
- 📖 **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Complete step-by-step instructions
- 💻 **[QUICKSTART.md](QUICKSTART.md)** - Windows-specific setup guide

**For deep understanding:**
- 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)** - How the system works internally
- 📄 **This README** - Full project documentation

## 🎯 Why This Tool Exists

As of 2026, GitHub has largely transitioned from "Classic Branch Protection" to **Repository Rulesets**. While classic protection still exists, Rulesets are the modern standard for enterprise compliance because they:
- Can be enforced at the **Organization level**
- Support **layered rules** (Org rule + Repo rule)
- Provide a unified API for compliance auditing

This tool uses the **aggregated rules endpoint** (`/repos/{owner}/{repo}/rules/branches/{branch}`) to audit the *actual, effective* protection state regardless of whether rules come from Classic Protection or Repository Rulesets.

## 🔐 SOC 2 Controls Mapped

| SOC 2 Common Criteria | GitHub Control | Purpose |
|----------------------|----------------|---------|
| **CC6.1 / CC8.1** (Change Management) | `pull_request_before_merging` | Prevents direct commits to production branches |
| **CC2.2** (Internal Oversight) | `required_approving_review_count ≥ 1` | Two-person rule: Independent code review required |
| **CC7.1** (System Operations) | `required_status_checks` | CI/CD gates must pass before merge |
| **CC6.8** (Software Integrity) | `required_signatures` | Cryptographically signed commits |
| *(Recommended)* | `non_fast_forward` | Linear history enforcement |

## 📋 Prerequisites

- **Python 3.10+**
- **GitHub Token**: Personal Access Token (PAT) or GitHub App Token with:
  - `repo:read` scope
  - `read:org` scope
- **Access**: Must have read access to the target organization

## 🚀 Quick Start

### For Windows Users (Easiest Method)

**See [QUICKSTART.md](QUICKSTART.md) for detailed Windows instructions!**

1. **Get your GitHub token**: https://github.com/settings/tokens (requires `repo:read` and `read:org` scopes)
2. **Edit `.env` file** with your organization name and token
3. **Run**: `run_auditor.bat` (basic) or `run_auditor.bat issues` (with auto-issue creation)

### Standard Setup (All Platforms)

#### 1. Install Dependencies

```bash
# Create virtual environment (if not exists)
python -m venv .venv

# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Environment

Edit the `.env` file (already created for you):

```bash
GITHUB_ORG=your-org-name
GITHUB_TOKEN=ghp_yourPersonalAccessToken
CREATE_ISSUES=false

# Optional secure secret sources (instead of GITHUB_TOKEN)
# GITHUB_TOKEN_FILE=/run/secrets/github_token
# GITHUB_TOKEN_COMMAND=aws secretsmanager get-secret-value --secret-id github/auditor/token --query SecretString --output text

# Optional GitHub App auth mode
# GITHUB_AUTH_MODE=app
# GITHUB_APP_ID=123456
# GITHUB_APP_INSTALLATION_ID=789012
# GITHUB_APP_PRIVATE_KEY_FILE=/run/secrets/github_app_private_key.pem
```

**Generate a token**: [https://github.com/settings/tokens](https://github.com/settings/tokens)

#### 3. Validate Setup (Recommended)

Before running the auditor, validate your configuration:

```bash
python validate_setup.py
```

This checks:
- ✅ Environment variables are set
- ✅ Python dependencies are installed
- ✅ GitHub token is valid
- ✅ Organization is accessible

If `GITHUB_AUTH_MODE=app`, the validator also checks GitHub App credentials and installation-token generation.

#### 4. Run the Auditor

**Basic auditor (CSV report only):**
```bash
python github_auditor.py
```

**Extended auditor (with auto-issue creation):**
```bash
python github_auditor_with_issues.py
```

**Or use the Windows batch file:**
```bash
run_auditor.bat          # Basic
run_auditor.bat issues   # With issues
```

### 5. Review the Report

The tool generates a CSV report: `github_audit_report_YYYYMMDD_HHMMSS.csv`

**Key columns:**
- `SOC2_COMPLIANT`: Overall pass/fail (TRUE/FALSE)
- `pull_request_before_merging`: PRs required
- `required_approving_review_count`: Code reviews enforced
- `required_status_checks`: CI/CD checks active
- `required_signatures`: Commit signing active
- `non_fast_forward`: Linear history enforced
- `issue_created`: Was GitHub issue created? (extended version only)
- `issue_number`: Issue number if created (extended version only)

**Open in Excel, Google Sheets, or filter with pandas to find non-compliant repos.**

## 📊 Sample Output

```
Starting SOC 2 Branch Protection Audit for Org: acme-corp
Fetched page 1 (42 repos)...
Found 42 active repositories. Scanning rules...

--- Audit Complete ---
Scanned: 42 repositories
Compliant: 38
Non-Compliant: 4
Report saved to: github_audit_report_20260203.csv
```

## 🔍 How It Works

1. **Fetches all active repositories** in your organization
2. **Queries the Rulesets API** for each repository's default branch
3. **Aggregates rules** from:
   - Organization-level Rulesets
   - Repository-level Rulesets
   - Classic Branch Protection (converted to standard format)
4. **Evaluates compliance** against SOC 2 control requirements
5. **Exports a CSV** with actionable findings

## 🎯 For Auditors

When working with firms like Coalfire, A-LIGN, or Drata:

1. **Population Testing**: The CSV represents your entire repository population
2. **Sample Selection**: Filter `SOC2_COMPLIANT=FALSE` to identify gaps
3. **Evidence Package**: Include:
   - The generated CSV report
   - Screenshot of script execution
   - GitHub Organization settings screenshot

## 🔄 Future-Proofing

This tool is designed for **2026 onwards** and handles:
- ✅ Legacy Classic Branch Protection (auto-converted by API)
- ✅ Modern Repository Rulesets
- ✅ Organization-level enforcement
- ✅ Layered rule stacks

**No code changes needed** when migrating from Classic → Rulesets.

## 🛠️ Advanced Usage

### Filter Specific Repositories

Modify `get_all_repos()` to filter by naming pattern:
```python
if repo['name'].startswith('prod-'):
    repos.append(repo)
```

### Adjust Compliance Thresholds

In `audit_repo()`, modify the compliance definition:
```python
# Require 2 reviewers instead of 1
results["SOC2_COMPLIANT"] = (
    results["pull_request_before_merging"] and 
    results["required_approving_review_count"] >= 2
)
```

### Rate Limit Handling

For large organizations (>1000 repos), consider:
```python
time.sleep(0.5)  # Increase delay between requests
```

## 📝 Next Steps

### Auto-Remediation (Coming Soon)

See [github_auditor_with_issues.py](github_auditor_with_issues.py) for automatic issue creation in non-compliant repositories.

## 🤝 Contributing

This tool is designed for SOC 2 compliance scenarios. Contributions welcome for:
- Additional SOC 2 Type 2 controls
- PCI-DSS mapping
- ISO 27001 controls
- Automated remediation workflows

## 📄 License

MIT License - Use freely for compliance auditing

## ⚠️ Security Notes

- **Never commit your `.env` file**
- Use environment variables for secrets
- Consider using GitHub Apps instead of PATs for production
- Rotate tokens regularly (90-day maximum)

## 📚 Additional Resources

- [GitHub Rulesets Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [SOC 2 Common Criteria](https://us.aicpa.org/interestareas/frc/assuranceadvisoryservices/socforserviceorganizations)
- [GitHub Branch Protection API](https://docs.github.com/en/rest/repos/rules)

---

**Built for SOC 2 compliance in 2026** | Questions? Open an issue.
