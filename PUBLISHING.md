# Publishing to PyPI

This guide walks through publishing the mental-rotation-research package to PyPI.

## Prerequisites

### 1. Create PyPI Accounts

- **PyPI** (production): https://pypi.org/account/register/
- **TestPyPI** (testing): https://test.pypi.org/account/register/

### 2. Enable 2FA and Create API Tokens

For security, PyPI requires 2FA (two-factor authentication):

1. Go to Account Settings → Add 2FA
2. After enabling 2FA, create an API token:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/
3. Save tokens securely (you'll only see them once!)

### 3. Install Publishing Tools

```bash
pip install --upgrade build twine
```

## Pre-Publishing Checklist

Before publishing, ensure:

- [ ] Email in `setup.py` is updated (currently `savantlab@example.com`)
- [ ] Version number is correct in `setup.py`
- [ ] README.md is complete and accurate
- [ ] LICENSE file exists
- [ ] CHANGELOG.md is updated
- [ ] All dependencies are listed in `install_requires`
- [ ] Package installs locally: `pip install -e .`
- [ ] CLI commands work: `mental-rotation-scrape --help`
- [ ] No sensitive data in repository
- [ ] `.gitignore` excludes `data/`, `dist/`, `build/`, `*.egg-info`

## Publishing Steps

### Step 1: Update Author Email

Edit `setup.py` and replace `savantlab@example.com` with your real email:

```python
author_email="your-email@domain.com",
```

### Step 2: Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### Step 3: Build the Package

```bash
python -m build
```

This creates two files in `dist/`:
- `mental-rotation-research-0.1.0.tar.gz` (source distribution)
- `mental_rotation_research-0.1.0-py3-none-any.whl` (wheel)

### Step 4: Test Upload to TestPyPI (Recommended)

First, test on TestPyPI to catch any issues:

```bash
python -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-...` (your TestPyPI API token)

**Or** configure credentials in `~/.pypirc`:

```ini
[testpypi]
  username = __token__
  password = pypi-AgEIcHlwaS5vcmc...your-token...

[pypi]
  username = __token__
  password = pypi-AgEIcHlwaS5vcmc...your-token...
```

### Step 5: Test Installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mental-rotation-research
```

(The `--extra-index-url` allows dependencies to be installed from real PyPI)

Test that it works:
```bash
mental-rotation-scrape --help
mental-rotation-reading list
```

### Step 6: Upload to PyPI (Production)

Once testing is successful:

```bash
python -m twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-...` (your PyPI API token)

### Step 7: Verify on PyPI

Your package should now be live at:
- https://pypi.org/project/mental-rotation-research/

Users can install it with:
```bash
pip install mental-rotation-research
```

## Updating the Package

When releasing a new version:

1. **Update version number** in `setup.py`:
   ```python
   version="0.1.1",  # or 0.2.0, 1.0.0, etc.
   ```

2. **Update CHANGELOG.md** with changes

3. **Commit changes**:
   ```bash
   git add setup.py CHANGELOG.md
   git commit -m "Bump version to 0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```

4. **Rebuild and upload**:
   ```bash
   rm -rf dist/ build/ *.egg-info
   python -m build
   python -m twine upload dist/*
   ```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

Examples:
- `0.1.0` → `0.1.1`: Bug fix
- `0.1.1` → `0.2.0`: New feature
- `0.2.0` → `1.0.0`: Breaking change or stable release

## Common Issues

### "Package name already exists"

The name `mental-rotation-research` might be taken. Try:
- `mental-rotation-tools`
- `mentalrotation-research`
- `mr-research-tools`

Update the name in `setup.py` and try again.

### "Invalid distribution filename"

Make sure you're in the project root and `setup.py` exists.

### "Twine not found"

Install it: `pip install twine`

### "README rendering failed"

Test your README locally:
```bash
python -m readme_renderer README.md -o /tmp/readme.html
```

### "Missing dependencies on TestPyPI"

Some dependencies might not be on TestPyPI. Use:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ your-package
```

## Security Best Practices

1. **Never commit API tokens** to git
2. **Use API tokens** instead of passwords
3. **Enable 2FA** on your PyPI account
4. **Use scoped tokens** for CI/CD (if applicable)
5. **Rotate tokens** periodically
6. **Review package contents** before uploading:
   ```bash
   tar -tzf dist/mental-rotation-research-0.1.0.tar.gz
   ```

## Useful Commands

```bash
# Check package metadata
python setup.py check

# View what will be included
python setup.py sdist --list-manifest

# Check distribution
twine check dist/*

# View PyPI packages
pip list

# Uninstall package
pip uninstall mental-rotation-research
```

## Resources

- **PyPI**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Docs**: https://twine.readthedocs.io/
- **Semantic Versioning**: https://semver.org/

## Quick Reference

```bash
# Complete publishing workflow
rm -rf dist/ build/ *.egg-info
python -m build
twine check dist/*
python -m twine upload --repository testpypi dist/*  # Test first
python -m twine upload dist/*                        # Then production
```
