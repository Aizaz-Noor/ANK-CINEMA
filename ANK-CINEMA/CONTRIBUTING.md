# Contributing to ANK-Cinema

Thanks for taking the time to contribute.

---

## Development Setup

```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA
cd ANK-CINEMA/ANK-CINEMA
pip install -e ".[dev]"
```

This installs the package in editable mode plus `pytest`, `black`, and `ruff`.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests must pass on Python 3.8+ and on all three platforms (Ubuntu, Windows, macOS).
The CI matrix covers 9 combinations — do not break any of them.

---

## Code Style

```bash
ruff check ank_cinema_core.py   # lint
black ank_cinema_core.py        # format
```

Line length is 90. All functions must have docstrings or inline comments explaining
the *why*, not just the *what*.

---

## Pull Request Guidelines

1. One PR per logical change — do not bundle unrelated fixes.
2. All tests must pass before requesting review.
3. If you add a function, add a test for it in `tests/test_core.py`.
4. Update `CHANGELOG.md` under `[Unreleased]` with a one-line description.
5. Keep commit messages short and factual:
   - `fix: handle empty magnet string in enrich_magnet`
   - `feat: add seeders column sort option`
   - `docs: expand architecture section in README`

---

## Reporting Bugs

Open a GitHub Issue with:
- OS and Python version
- The contents of `logs/error.log` (if present)
- Steps to reproduce
