# GitHub Setup Guide

This guide will help you publish this repository to GitHub.

## Pre-Flight Checklist

✅ **Environment Variables Protected**
- `.env` is in `.gitignore` (never commit secrets!)
- `.env.example` provided as a template

✅ **Sensitive Files Excluded**
- All API keys and credentials are in `.env` (not in code)
- `data/` and `logs/` directories are ignored
- `venv/` is ignored

✅ **Documentation Complete**
- README.md with setup instructions
- LICENSE file (MIT)
- Documentation in `docs/` folder

## Publishing to GitHub

### 1. Initialize Git Repository (if not already done)

```bash
cd /Users/david.darkins/IDE/lotr
git init
```

### 2. Add All Files

```bash
git add .
```

**Important:** Verify that `.env` is NOT being added:
```bash
git status | grep .env
# Should show nothing (or show .env.example only)
```

### 3. Create Initial Commit

```bash
git commit -m "Initial commit: LOTR Data Cloud POC

- Python Flask app for ingesting LOTR data into Salesforce Data Cloud
- Two-step OAuth token exchange implementation
- Streaming ingestion API integration
- Bulk deletion API support
- Data Cloud Related Lists demonstration
- Complete documentation and setup guides"
```

### 4. Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository (e.g., `lotr-data-cloud-poc`)
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)

### 5. Connect and Push

```bash
git remote add origin https://github.com/YOUR_USERNAME/lotr-data-cloud-poc.git
git branch -M main
git push -u origin main
```

## Post-Publish Checklist

- [ ] Verify `.env` is NOT in the repository
- [ ] Test cloning the repo in a fresh directory
- [ ] Verify `.env.example` is visible
- [ ] Check that all documentation links work
- [ ] Update README with your GitHub repo URL (if needed)

## Security Reminders

⚠️ **NEVER commit:**
- `.env` file
- Any file containing API keys or secrets
- Salesforce access tokens
- Personal credentials

✅ **Safe to commit:**
- `.env.example` (template only)
- All Python code
- Documentation
- Schema files
- Configuration templates

## Adding GitHub Badges (Optional)

Once published, you can add badges to your README:

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Salesforce](https://img.shields.io/badge/Salesforce-Data%20Cloud-00A1E0.svg)
```

## CI/CD (Optional)

A basic GitHub Actions workflow is included in `.github/workflows/ci.yml` for Python linting. It will run automatically on push and pull requests.

