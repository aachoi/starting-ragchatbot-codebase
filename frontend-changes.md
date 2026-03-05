# Frontend Changes — Code Quality Tooling

## Overview

Added Prettier for automatic code formatting and a quality check script for the frontend (HTML/CSS/JS). This mirrors the role that `black` plays for Python backends, but applied to the frontend layer only.

## Files Added

### `frontend/package.json`
- Defines the frontend as an npm package (`ragchatbot-frontend`).
- Adds `prettier` as a dev dependency.
- Provides three npm scripts:
  - `npm run format` — auto-format all frontend files in-place.
  - `npm run format:check` — check formatting without modifying files (CI-friendly).
  - `npm run quality` — alias for `format:check`.

### `frontend/.prettierrc`
- Configures Prettier with consistent rules:
  - 2-space indentation, no tabs.
  - 80-character print width.
  - Single quotes in JS.
  - Trailing commas where valid in ES5 (objects, arrays, function params).
  - LF line endings.
  - CSS-sensitivity mode for HTML whitespace.

### `scripts/check-frontend.sh`
- Bash script that runs the full frontend quality check from the repo root.
- Auto-installs npm dependencies if `node_modules` is absent.
- Exits with a non-zero code if any file is not properly formatted (safe for CI).
- Prints a reminder of the auto-fix command on success.

## Files Modified

### `frontend/script.js`
- Removed stale comment (`// Removed removeMessage function...`).
- Removed double blank line in `setupEventListeners`.
- Normalised indentation inside `try/catch` blocks to 2-space (Prettier standard).
- Added trailing commas to object literals inside `fetch` calls.
- Reformatted chained `.map().join()` call for `sourceLinks` to multi-line for readability.
- Changed arrow-function params from `button =>` to `(button) =>` (Prettier default).
- Broke long `getElementById(...).addEventListener(...)` chain across two lines.

### `frontend/style.css`
- Fixed reference to undefined CSS variable `var(--primary)` in `.message-content blockquote` — changed to the correct `var(--primary-color)`.

## How to Use

```bash
# Check formatting (read-only, exits non-zero if files need formatting)
./scripts/check-frontend.sh

# Auto-format all frontend files
cd frontend && npm run format

# Or install deps first if needed
cd frontend && npm install && npm run format
```
