# Frontend Changes

## Code Quality Tooling

Added Prettier for automatic code formatting and a quality check script for the frontend (HTML/CSS/JS). This mirrors the role that `black` plays for Python backends, but applied to the frontend layer only.

### Files Added

#### `frontend/package.json`
- Defines the frontend as an npm package (`ragchatbot-frontend`).
- Adds `prettier` as a dev dependency.
- Provides three npm scripts:
  - `npm run format` — auto-format all frontend files in-place.
  - `npm run format:check` — check formatting without modifying files (CI-friendly).
  - `npm run quality` — alias for `format:check`.

#### `frontend/.prettierrc`
- Configures Prettier with consistent rules:
  - 2-space indentation, no tabs.
  - 80-character print width.
  - Single quotes in JS.
  - Trailing commas where valid in ES5 (objects, arrays, function params).
  - LF line endings.
  - CSS-sensitivity mode for HTML whitespace.

#### `scripts/check-frontend.sh`
- Bash script that runs the full frontend quality check from the repo root.
- Auto-installs npm dependencies if `node_modules` is absent.
- Exits with a non-zero code if any file is not properly formatted (safe for CI).
- Prints a reminder of the auto-fix command on success.

### How to Use

```bash
# Check formatting (read-only, exits non-zero if files need formatting)
./scripts/check-frontend.sh

# Auto-format all frontend files
cd frontend && npm run format

# Or install deps first if needed
cd frontend && npm install && npm run format
```

---

## Dark/Light Theme Toggle

Added a dark/light theme toggle button that persists user preference via `localStorage`.

### Files Modified

#### `frontend/index.html`
- Added a `<button class="theme-toggle" id="themeToggle">` element directly inside `<body>`, before `.container`.
- Button contains two inline SVG icons:
  - `.icon-moon` — shown in dark mode; click switches to light.
  - `.icon-sun` — shown in light mode; click switches to dark.
- Button has `aria-label` and `title` attributes for accessibility and keyboard navigation.

#### `frontend/style.css`
1. **Light theme CSS variables** — added `[data-theme="light"]` block with:
   - `--background: #f8fafc` (near-white)
   - `--surface: #ffffff`
   - `--surface-hover: #f1f5f9`
   - `--text-primary: #0f172a` (dark slate for contrast)
   - `--text-secondary: #64748b`
   - `--border-color: #e2e8f0`
   - `--assistant-message: #f1f5f9`
   - `--shadow` adjusted for lighter environments
   - `--theme-toggle-bg/color/hover-bg` variants for both themes

2. **Toggle button styles** (`.theme-toggle`) — fixed position, top-right corner:
   - 40×40px circle, inherits theme variables
   - Hover: slight scale + shadow
   - Focus: accessible focus ring using `--focus-ring`
   - Icon visibility toggled via CSS: `.icon-moon` hides and `.icon-sun` shows under `[data-theme="light"]`

3. **Smooth transitions** — added `transition: background-color 0.3s ease, ...` to:
   - `body`, `.sidebar`, `.chat-main`, `.chat-container`, `.chat-messages`, `.chat-input-container`, `.message-content`, `.stat-item`, `.suggested-item`, `#chatInput`, `.source-pill`

4. **CSS variable fix** — Fixed reference to undefined `var(--primary)` in `.message-content blockquote` — changed to the correct `var(--primary-color)`.

#### `frontend/script.js`
- `initTheme()` — reads `localStorage.getItem('theme')` on page load; applies `data-theme="light"` to `<html>` if saved.
- `toggleTheme()` — toggles `data-theme` attribute on `document.documentElement` and persists choice to `localStorage`.
- Both called inside `DOMContentLoaded`; toggle button wired via event listener in `setupEventListeners()`.

### Behaviour
- Default theme: **dark** (no `data-theme` attribute).
- Clicking the button toggles to light/dark and saves the preference.
- On reload, the saved theme is restored before first paint (no flash).
- All existing elements use CSS custom properties, so they adapt automatically.
