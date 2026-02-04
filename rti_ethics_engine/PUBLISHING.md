# 🚀 How to Host and Publish RTI Ethics Engine to PyPI

Congratulations! Your package is built and ready for the world. Follow these steps to make it available via `pip install rti-ethics-engine`.

---

## 1. Create a PyPI Account

If you don't have one, create an account on [PyPI (Python Package Index)](https://pypi.org/account/register/).

## 2. Generate an API Token

PyPI now requires API tokens for secure uploads (passwords no longer work for `twine`).

1. Log in to [PyPI](https://pypi.org/).
2. Go to **Account Settings** > **API tokens**.
3. Create a new token with "Entire account" scope (or specific project if it already exists).
4. **Copy the token immediately** (it starts with `pypi-`). You won't see it again!

## 3. Verify the Build

I've already run the build for you. You should see a `dist/` folder in the package directory containing:

- `rti_ethics_engine-1.0.0.tar.gz` (Source)
- `rti_ethics_engine-1.0.0-py3-none-any.whl` (Wheel)

To rebuild manually:

```bash
python -m build
```

## 4. Upload to PyPI

Run the following command in the `rti_ethics_engine` folder:

```bash
python -m twine upload dist/*
```

- **Username**: Use `__token__`
- **Password**: Paste your API token (including the `pypi-` prefix)

## 5. Verify Installation

Wait a minute or two, then anyone can install it!

```bash
pip install rti-ethics-engine
```

---

## 💡 Pro Tips

### Test Before Real Publish

Use **TestPyPI** to avoid using up version numbers on mistakes:

1. Register on [TestPyPI](https://test.pypi.org/).
2. Upload: `python -m twine upload --repository testpypi dist/*`
3. Install: `pip install --index-url https://test.pypi.org/simple/ rti-ethics-engine`

### Bumping Versions

When you make changes:

1. Update `version = "1.0.1"` in `pyproject.toml`.
2. Delete the old `dist/` folder.
3. Run `python -m build` again.
4. Upload the new files.

### Automation

The package already includes a `.github/workflows/ci.yml` file. If you host this on GitHub, you can set up "GitHub Actions" to publish automatically whenever you create a new "Release" or "Tag".
