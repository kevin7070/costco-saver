# Quality gate for costco-saver
#
# Usage:
#   make check                  — Full: lint + backend tests + coverage + frontend build. Use before push.
#   make test                   — Backend tests + coverage only
#   make coverage               — Detailed backend coverage report
#   make quick                  — Backend tests only (no coverage, fast)
#   make build                  — Frontend production build only
#   make check-no-google-fonts  — Guard: no third-party font CDN references in backend HTML/PDF/Python

.PHONY: check test coverage quick build check-no-google-fonts

# Adding a guard to `check:` auto-gates CI (workflow invokes the same
# Makefile targets). Single source of truth — do not duplicate the gate
# definition between Makefile and .gitea/workflows/ci.yml.
check: check-no-google-fonts test build
	@echo ""
	@echo "✓ All checks passed"

test:
	@echo "→ Backend: pytest + coverage"
	cd backend && .venv/bin/python -m pytest tests/ -q

coverage:
	@echo "→ Backend: detailed coverage report"
	cd backend && .venv/bin/python -m pytest tests/ --cov-report=term-missing

quick:
	@echo "→ Backend: pytest (no coverage)"
	cd backend && .venv/bin/python -m pytest tests/ -q --no-cov

build:
	@echo "→ Frontend: npm run build"
	cd frontend && npm run build --silent

# Regression guard against re-introducing third-party Google Fonts CDN
# dependencies in backend HTML/PDF/Python code. Email templates MUST use
# a system-font fallback chain; PDF rendering should self-host webfonts
# via @font-face + file:// URLs. Intentional docstring references can be
# exempted with `# noqa: googlefonts-check` on the same line.
check-no-google-fonts:
	@echo "→ Backend: check-no-google-fonts (HTML/PDF font self-host guard)"
	@if grep -rnE "fonts\.(googleapis|gstatic)\.com" backend/apps/ \
	     --include="*.html" --include="*.py" \
	     --exclude-dir=__pycache__ \
	     | grep -v "noqa: googlefonts-check" ; then \
	  echo ""; \
	  echo "✗ FAIL: found Google Fonts CDN references — see lines above."; \
	  echo "  Email templates: system-font chain only."; \
	  echo "  PDF/HTML: self-host via @font-face + file:// URLs."; \
	  echo "  Intentional historic mentions: add '# noqa: googlefonts-check' on the same line."; \
	  exit 1; \
	fi
	@echo "✓ check-no-google-fonts: clean"
