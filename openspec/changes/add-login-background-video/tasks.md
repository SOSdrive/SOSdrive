## 1. Background media

- [x] 1.1 Reuse the existing login screen and define one replaceable background-video source using the MP4 already under `assets/`; verify the configured URL resolves to the local asset.
- [x] 1.2 Add a decorative video element with autoplay, loop, muted, and inline-playback attributes; verify the rendered login page includes all four attributes and cover sizing.

## 2. Login layout and contrast

- [x] 2.1 Add the full-viewport video layer, dark overlay, poster/CSS fallback, and non-intercepting stacking order in the existing shared styles; verify the form appears above both layers and remains clickable.
- [x] 2.2 Adapt the existing login layout to keep the solid, rounded form card left-aligned and responsive; verify the card and controls remain within desktop and mobile viewports.

## 3. Verification

- [x] 3.1 Verify the login page with a playing video and an unavailable source; confirm muted autoplay attributes, poster/CSS fallback availability, contrast, responsive layout, and working login-page navigation.
