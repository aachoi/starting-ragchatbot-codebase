# Frontend Changes: Dark/Light Theme Toggle

## Summary
Added a dark/light theme toggle button that persists user preference via `localStorage`.

---

## Files Modified

### `frontend/index.html`
- Added a `<button class="theme-toggle" id="themeToggle">` element directly inside `<body>`, before `.container`.
- Button contains two inline SVG icons:
  - `.icon-moon` — shown in dark mode; click switches to light.
  - `.icon-sun` — shown in light mode; click switches to dark.
- Button has `aria-label` and `title` attributes for accessibility and keyboard navigation.

### `frontend/style.css`
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

### `frontend/script.js`
- `initTheme()` — reads `localStorage.getItem('theme')` on page load; applies `data-theme="light"` to `<html>` if saved.
- `toggleTheme()` — toggles `data-theme` attribute on `document.documentElement` and persists choice to `localStorage`.
- Both called inside `DOMContentLoaded`; toggle button wired via event listener in `setupEventListeners()`.

---

## Behaviour
- Default theme: **dark** (no `data-theme` attribute).
- Clicking the button toggles to light/dark and saves the preference.
- On reload, the saved theme is restored before first paint (no flash).
- All existing elements use CSS custom properties, so they adapt automatically.