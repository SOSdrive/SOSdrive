## Why

A landing page already exists in Python/Reflex, but its hero is visually flat: content is stacked without layered depth, a strong typographic scale, or the calm visual richness expected from a modern emergency-assistance product. The page needs a reusable visual foundation before the operational Home and future screens are built on top of it.

## What Changes

- Refactor only the landing page hero presentation layer without changing its existing content or copy.
- Add layered orange and trust-blue glow blobs behind the hero content.
- Add optional transparent local illustrations with independent floating motion and silent fallbacks when assets are missing.
- Convert the “Visão da assistência” panel and future highlight cards to a reusable glassmorphism treatment.
- Strengthen hero typography, spacing, headline scale, and orange keyword emphasis.
- Style trust chips as translucent pills with hover elevation.
- Style the primary CTA with an emergency-orange gradient, colored shadow, and restrained hover elevation.
- Extract shared visual tokens and CSS injection helpers into a reusable Python style module for future screens.
- Add `prefers-reduced-motion` rules that disable all glow and illustration animation.
- Keep the implementation entirely in Python + Reflex, with no Node service, React/Vue app, 3D engine, or external renderer.

## Capabilities

### New Capabilities

- `web/landing-hero-visual-system`: Layered, animated, accessible landing hero presentation and reusable visual style primitives.

### Modified Capabilities

- None. The existing landing content remains behaviorally unchanged; this change adds a new visual capability.

## Impact

- **Frontend**: `presentation_screen.py` and a shared Python style module such as `styles.py`.
- **Assets**: optional transparent PNG/WebP illustrations under `assets/`; missing assets must not break rendering.
- **Runtime**: CSS is defined through Reflex global styles from Python. No backend stack change.
- **Dependencies**: no new Python package is required.
- **Future reuse**: the shared tokens and classes remain available to future screens without coupling them to the landing.
