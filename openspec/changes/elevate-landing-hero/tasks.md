## 1. Shared visual foundation

- [x] 1.1 Create `styles.py` with SOS Drive color/type/spacing tokens and verify it imports without requiring Streamlit app execution
- [x] 1.2 Add `load_local_asset_data_uri` for PNG/WebP assets with silent missing-file fallback and verify absent assets produce no exception or broken markup
- [x] 1.3 Add scoped CSS injection for glow, glass, chips, CTA, focus, responsive behavior, and `prefers-reduced-motion`; verify selectors do not alter unrelated Streamlit pages

## 2. Landing hero refactor

- [x] 2.1 Wrap the existing hero content in a layered visual container without changing copy or content order; verify all existing headings, panel text, chips, and CTA remain present
- [x] 2.2 Add orange and trust-blue glow blobs with independent pulse delays; verify they remain behind content and do not reduce text contrast
- [x] 2.3 Add optional local transparent illustrations with independent float animations and fallback behavior; verify the hero works with zero assets
- [x] 2.4 Apply reusable glassmorphism to “Visão da assistência” and verify translucent fallback when backdrop blur is unavailable
- [x] 2.5 Apply stronger headline scale, orange keyword emphasis, chip hover elevation, and orange-family CTA gradient/shadow; verify focus and hover states

## 3. Responsive and accessibility validation

- [x] 3.1 Validate desktop layout in the running Streamlit app and verify no horizontal overflow
- [x] 3.2 Validate mobile viewport layout and verify CTA, chips, and assistance panel remain readable and reachable
- [x] 3.3 Validate keyboard focus order and effective text contrast; verify normal text reaches at least 4.5:1
- [x] 3.4 Validate `prefers-reduced-motion` and verify glow/illustration animations are disabled

## 4. Reuse and verification

- [x] 4.1 Document how the shared style module can be reused by future screens without importing landing-specific content
- [x] 4.2 Run `python -m py_compile presentation_screen.py styles.py` and confirm no syntax errors
- [x] 4.3 Run `openspec validate elevate-landing-hero --type change --strict` and confirm the change is valid
