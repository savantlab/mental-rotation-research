# Publishing Checklist for mental-rotation-research

Use this checklist when you're ready to publish to PyPI.

## ✅ Pre-Publishing (Do Once)

- [ ] Create PyPI account at https://pypi.org/account/register/
- [ ] Create TestPyPI account at https://test.pypi.org/account/register/
- [ ] Enable 2FA on both accounts
- [ ] Create PyPI API token: https://pypi.org/manage/account/token/
- [ ] Create TestPyPI API token: https://test.pypi.org/manage/account/token/
- [ ] Save tokens securely (you'll only see them once)

## ✅ Package Preparation

- [ ] Update `author_email` in `setup.py` (currently: `savantlab@example.com`)
- [ ] Verify version number is correct in `setup.py` (currently: `0.1.0`)
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Ensure README.md is complete
- [ ] Test package installs locally: `pip install -e .`
- [ ] Test CLI commands work:
  ```bash
  mental-rotation-scrape --help
  mental-rotation-analyze --help
  mental-rotation-reading list
  ```

## ✅ Build Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build distributions
python -m build

# Verify build
ls -lh dist/

# Should see:
# - mental_rotation_research-0.1.0-py3-none-any.whl
# - mental_rotation_research-0.1.0.tar.gz

# Check distributions
python -m twine check dist/*

# Should show: PASSED for both files
```

## ✅ Test on TestPyPI (Recommended First Time)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# When prompted:
# Username: __token__
# Password: pypi-... (your TestPyPI token)

# Test installation
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            mental-rotation-research

# Verify it works
mental-rotation-reading list
```

**Note**: If the package name is already taken, you'll need to choose a different name in `setup.py`.

## ✅ Publish to PyPI (Production)

```bash
# Upload to PyPI
python -m twine upload dist/*

# When prompted:
# Username: __token__
# Password: pypi-... (your PyPI token)
```

## ✅ Post-Publishing

- [ ] Verify package appears at: https://pypi.org/project/mental-rotation-research/
- [ ] Test installation from PyPI:
  ```bash
  pip install mental-rotation-research
  ```
- [ ] Create Git tag for release:
  ```bash
  git tag v0.1.0
  git push origin v0.1.0
  ```
- [ ] Create GitHub release with notes from CHANGELOG.md
- [ ] Update README.md to reflect PyPI availability
- [ ] Announce release (if desired)

## 🚀 Alternative: Using .pypirc (Optional)

To avoid entering credentials each time, create `~/.pypirc`:

```ini
[testpypi]
  username = __token__
  password = pypi-AgEIcHlwaS5vcmc...your-testpypi-token...

[pypi]
  username = __token__
  password = pypi-AgEIcHlwaS5vcmc...your-pypi-token...
```

Then you can upload without prompts:
```bash
python -m twine upload --repository testpypi dist/*  # TestPyPI
python -m twine upload dist/*                        # PyPI
```

**Security**: Make sure `.pypirc` is not committed to git!

## 📝 Current Status

- ✅ Package structure created
- ✅ Build tools installed (`build`, `twine`)
- ✅ Test build successful
- ✅ Distributions validated (PASSED)
- ⏸️ Email address needs updating in setup.py
- ⏸️ PyPI accounts need to be created
- ⏸️ API tokens need to be generated
- ⏸️ Ready to upload once above complete

## 🔄 For Future Updates

When releasing version 0.1.1, 0.2.0, etc.:

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Clean and rebuild:
   ```bash
   rm -rf dist/ build/ *.egg-info
   python -m build
   twine check dist/*
   ```
4. Upload:
   ```bash
   python -m twine upload dist/*
   ```
5. Tag release:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```

## 📚 Quick Reference

| Command | Purpose |
|---------|---------|
| `python -m build` | Build package distributions |
| `twine check dist/*` | Validate distributions |
| `twine upload --repository testpypi dist/*` | Upload to TestPyPI |
| `twine upload dist/*` | Upload to PyPI |
| `pip install mental-rotation-research` | Install from PyPI |

## ❓ Help

See `PUBLISHING.md` for detailed guide including:
- Common issues and solutions
- Security best practices
- Version numbering guidelines
- Full workflow examples
