# Security Fix: API Key Leak

## Immediate Actions Required

### 1. **REVOKE THE EXPOSED API KEY** (Do this FIRST!)
1. Go to https://platform.openai.com/api-keys
2. Find the exposed API key
3. Click "Revoke" or delete it immediately
4. Create a new API key

### 2. Remove Secrets from Git History

The API key was leaked in:
- `.env` file (if committed)
- `logs/00_pipeline_2025-12-19_16-17-35.log` (commit 0ac1bf3)

You need to remove ALL files containing secrets from git history:

#### Option A: Using git filter-repo (Recommended)

```bash
# Install git-filter-repo if not already installed
pip install git-filter-repo

# Remove .env and log files from entire git history
git filter-repo --path .env --path logs/ --invert-paths --force

# Or remove specific log file:
git filter-repo --path logs/00_pipeline_2025-12-19_16-17-35.log --invert-paths --force

# Force push to update remote (WARNING: This rewrites history!)
git push origin --force --all
```

#### Option B: Using BFG Repo-Cleaner (Alternative)

```bash
# Download BFG from https://rtyley.github.io/bfg-repo-cleaner/
# Remove .env and log files
java -jar bfg.jar --delete-files .env
java -jar bfg.jar --delete-folders logs

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

#### Option C: Manual removal (If above don't work)

```bash
# Remove .env and logs/ from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env logs/00_pipeline_2025-12-19_16-17-35.log" \
  --prune-empty --tag-name-filter cat -- --all

# Or remove entire logs directory:
git filter-branch --force --index-filter \
  "git rm -r --cached --ignore-unmatch logs/" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

### 3. Verify .gitignore is Complete

Check that `.env` and `logs/` are in `.gitignore`:

```bash
# Check .env is ignored
cat .gitignore | grep "\.env"

# Check logs are ignored (should have *.log and logs/)
cat .gitignore | grep -E "\.log|logs/"
```

If `logs/` directory is not explicitly ignored, add it:

```bash
# Add logs/ directory to .gitignore
echo "logs/" >> .gitignore
git add .gitignore
git commit -m "Add logs/ directory to .gitignore"
```

### 4. Update Local .env File

After revoking the old key, update your local `.env` file with the new API key:

```bash
# Make sure .env exists locally (not tracked by git)
echo "OPENAI_API_KEY=your_new_api_key_here" > .env
```

### 5. Verify No Other Secrets Are Exposed

Check for other potential secrets in git history:

```bash
# Search for API keys in git history
git log -p --all -S "sk-" | grep -E "sk-[a-zA-Z0-9]{20,}"

# Search in specific files/directories
git log -p --all -- "logs/*.log" | grep -E "sk-[a-zA-Z0-9]{20,}"
git log -p --all -- ".env" | grep -E "sk-[a-zA-Z0-9]{20,}"

# Search for other common secret patterns
git log -p --all | grep -E "(api[_-]?key|password|secret|token)" -i

# Check all log files in git
git ls-files logs/
```

## Prevention

### Already in place:
- ✅ `.env` is in `.gitignore`
- ✅ Code uses environment variables (not hardcoded keys)

### Additional recommendations:

1. **Use GitHub Secrets** for CI/CD if you have any
2. **Use git-secrets** to prevent committing secrets:
   ```bash
   git secrets --install
   git secrets --register-aws
   ```
3. **Use pre-commit hooks** to scan for secrets before commits
4. **Regular audits**: Use tools like GitGuardian or truffleHog

## After Fixing

1. ✅ Revoke old API key
2. ✅ Remove .env from git history
3. ✅ Create new API key
4. ✅ Update local .env file
5. ✅ Test that everything still works
6. ✅ Monitor for any unauthorized usage

## Important Notes

- **Force pushing rewrites history** - coordinate with team members
- **All collaborators** need to re-clone or reset their local repos after force push
- **The exposed key is compromised** - even after removing from git, it was visible on GitHub
- **Monitor your OpenAI usage** for any suspicious activity

