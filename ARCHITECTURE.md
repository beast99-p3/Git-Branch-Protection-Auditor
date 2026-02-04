# Project Architecture & Flow

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Computer                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  github_auditor.py                                 │    │
│  │  (or github_auditor_with_issues.py)                │    │
│  │                                                     │    │
│  │  1. Reads .env configuration                       │    │
│  │  2. Authenticates with GitHub API                  │    │
│  │  3. Fetches all org repositories                   │    │
│  │  4. Analyzes branch protection rules               │    │
│  │  5. Generates CSV report                           │    │
│  │  6. (Optional) Creates GitHub issues               │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   │                                          │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    │ HTTPS API Calls
                    │ (Authorization: Bearer TOKEN)
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  GitHub REST API                             │
│              (api.github.com)                                │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Endpoints Used:                                    │   │
│  │                                                      │   │
│  │  GET /orgs/{org}/repos                             │   │
│  │  → Returns list of all repositories                │   │
│  │                                                      │   │
│  │  GET /repos/{owner}/{repo}/rules/branches/{branch} │   │
│  │  → Returns EFFECTIVE branch protection rules       │   │
│  │    (aggregates Classic + Rulesets)                 │   │
│  │                                                      │   │
│  │  POST /repos/{owner}/{repo}/issues (optional)      │   │
│  │  → Creates compliance issue in repo                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Execution Flow

### Phase 1: Setup & Authentication
```
┌─────────────────┐
│ Script Starts   │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Load .env file      │
│ - GITHUB_ORG        │
│ - GITHUB_TOKEN      │
│ - CREATE_ISSUES     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Initialize GitHub   │
│ API client with     │
│ Bearer token auth   │
└────────┬────────────┘
         │
         ▼
```

### Phase 2: Repository Discovery
```
┌──────────────────────────┐
│ Call: GET /orgs/{org}/   │
│       repos?per_page=100 │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐     ┌───────────────┐
│ Paginated results:       │────▶│ More pages?   │
│ Page 1: 100 repos        │     │ Yes → Fetch   │
│ Page 2: 100 repos        │◀────│ No  → Continue│
│ Page 3: 42 repos (last)  │     └───────────────┘
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Filter out:              │
│ - Archived repos         │
│ - Disabled repos         │
└────────┬─────────────────┘
         │
         ▼
    [242 Active Repos]
```

### Phase 3: Compliance Analysis (per repository)
```
For each repository:

┌─────────────────────────────────────┐
│ Get default branch name             │
│ (usually 'main' or 'master')        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ API Call: GET /repos/{owner}/{repo}/│
│          rules/branches/{branch}    │
│                                     │
│ Returns: Array of rule objects      │
│ Example:                            │
│ [                                   │
│   {                                 │
│     "type": "pull_request",         │
│     "parameters": {                 │
│       "required_approving_review_   │
│         count": 2                   │
│     }                               │
│   },                                │
│   {                                 │
│     "type": "required_status_checks"│
│   }                                 │
│ ]                                   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Parse rules and check:              │
│                                     │
│ ✅ pull_request_before_merging      │
│    → Found "pull_request" type     │
│                                     │
│ ✅ required_approving_review_count  │
│    → Check parameters.required_    │
│      approving_review_count >= 1   │
│                                     │
│ ❌ required_status_checks           │
│    → "required_status_checks" type │
│      not found in rules            │
│                                     │
│ ❌ required_signatures              │
│ ❌ non_fast_forward                 │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Calculate SOC2_COMPLIANT:           │
│                                     │
│ IF (pull_request_before_merging AND │
│     required_approving_review_count)│
│   THEN COMPLIANT = TRUE             │
│   ELSE COMPLIANT = FALSE            │
│                                     │
│ Result: FALSE (missing reviews)     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ IF CREATE_ISSUES=true AND           │
│    COMPLIANT=false                  │
│                                     │
│ THEN:                               │
│   POST /repos/{owner}/{repo}/issues │
│   Body: Compliance gap details     │
│   Labels: security, compliance, etc │
│                                     │
│ Result: Issue #123 created         │
└────────┬────────────────────────────┘
         │
         ▼
   [Store results in array]
```

### Phase 4: Report Generation
```
┌─────────────────────────────────────┐
│ All repos analyzed                  │
│ Results: List of dictionaries       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Convert to Pandas DataFrame         │
│                                     │
│ Columns:                            │
│ - repo_name                         │
│ - SOC2_COMPLIANT                    │
│ - default_branch                    │
│ - pull_request_before_merging       │
│ - required_approving_review_count   │
│ - required_status_checks            │
│ - required_signatures               │
│ - non_fast_forward                  │
│ - visibility                        │
│ - audit_timestamp                   │
│ - issue_created (if applicable)     │
│ - issue_number (if applicable)      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Export to CSV:                      │
│ github_audit_report_20260203_       │
│   143052.csv                        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Print Summary:                      │
│                                     │
│ Scanned: 242 repositories           │
│ ✅ Compliant: 215                   │
│ ❌ Non-Compliant: 27                │
│ 📋 Issues Created: 27               │
└─────────────────────────────────────┘
```

## 🎯 Data Flow Example

### Input (Environment Variables)
```
GITHUB_ORG=acme-corp
GITHUB_TOKEN=ghp_abc123...
CREATE_ISSUES=true
```

### Processing
```
Repository: frontend-app
Default Branch: main

API Response from /rules/branches/main:
[
  {
    "type": "pull_request",
    "parameters": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews_on_push": true,
      "require_code_owner_review": false
    }
  }
]

Analysis:
✅ pull_request_before_merging: TRUE (found pull_request rule)
✅ required_approving_review_count: TRUE (count = 1)
❌ required_status_checks: FALSE (not in rules)
❌ required_signatures: FALSE (not in rules)
❌ non_fast_forward: FALSE (not in rules)

Compliance Result:
SOC2_COMPLIANT: TRUE (has PRs + reviews)
```

### Output (CSV Row)
```csv
repo_name,SOC2_COMPLIANT,default_branch,pull_request_before_merging,required_approving_review_count,required_status_checks,required_signatures,non_fast_forward,visibility,audit_timestamp,issue_created,issue_number
frontend-app,TRUE,main,TRUE,TRUE,FALSE,FALSE,FALSE,private,2026-02-03T14:30:52,FALSE,
```

## 🔐 Security Model

### Token Scopes Required
```
┌─────────────────────────────────────┐
│ Personal Access Token (PAT)         │
│                                     │
│ Required Scopes:                    │
│                                     │
│ ✅ repo                             │
│    └─ Grants: Read repository data │
│       - Branch protection rules     │
│       - Repository metadata         │
│       - (Write if creating issues)  │
│                                     │
│ ✅ read:org                         │
│    └─ Grants: List org repos       │
│       - Organization membership     │
│       - Team information            │
└─────────────────────────────────────┘
```

### Authentication Flow
```
1. Token stored in .env (never committed)
2. Loaded into environment variable
3. Sent in HTTP header:
   Authorization: Bearer ghp_abc123...
4. GitHub validates token on each request
5. Rate limit: 5,000 requests/hour (authenticated)
```

## ⚡ Performance Characteristics

### Time Complexity
```
Discovery:  O(n/100) API calls  where n = number of repos
Analysis:   O(n) API calls      one per repository
Reporting:  O(n) memory         pandas DataFrame

Example for 250 repositories:
- Discovery: 3 API calls (250/100 = 3 pages)
- Analysis:  250 API calls
- Total:     253 API calls
- Time:      ~75 seconds (with 0.3s delay per call)
```

### Rate Limiting
```
GitHub API Limits (Authenticated):
- 5,000 requests per hour
- Reset every hour

This tool uses ~1 request per repository:
- Can audit up to 4,500 repos per hour
- Includes 0.3s delay to be respectful

For 250 repos: 250 requests = 5% of hourly limit
```

## 📂 File Structure

```
Git Branch Protection Auditor/
│
├── .env                          # Your config (DO NOT COMMIT)
├── .env.example                  # Template for .env
├── .gitignore                    # Protects .env from git
│
├── requirements.txt              # Python dependencies
│
├── github_auditor.py             # Core auditor (CSV only)
├── github_auditor_with_issues.py # Extended (CSV + issues)
├── validate_setup.py             # Pre-flight checks
│
├── run_auditor.bat               # Windows quick-run script
│
├── README.md                     # Full documentation
├── QUICKSTART.md                 # Windows getting started
├── ARCHITECTURE.md               # This file (how it works)
│
└── github_audit_report_*.csv     # Generated reports (gitignored)
```

---

**Built for SOC 2 compliance in 2026** | Architecture questions? Open an issue.
