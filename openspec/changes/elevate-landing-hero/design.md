## Context

See proposal.md for the motivation. The landing page runs as a Python/Reflex app and has the required hero content, assistance panel, trust chips, CTA, and “Como funciona” section. The implementation must preserve those texts without introducing a separate operational flow.

## Goals / Non-Goals

**Goals:**

- Add depth through intentional background layers rather than unrelated decoration.
- Provide a reusable Python design system for colors, surfaces, motion, spacing, and focus states.
- Keep the page responsive for desktop and mobile widths.
- Preserve contrast and content legibility above all decorative layers.
- Make all optional images resilient to absent files.

**Non-Goals:**

- No copywriting, information-architecture, or navigation change.
- No map, GPS, provider, authentication, or operational Home behavior.
- No JavaScript framework, server, external image CDN, 3D model, Spline, or new package dependency.

## Decisions

### 1. Shared Python style module

**Decision:** Create a small `styles.py` module with color/type/spacing tokens, a `load_local_asset_data_uri` helper, and an `inject_design_system()` function. The landing page calls this function once.

**Rationale:** Shared Python tokens prevent visual drift and make the same glass, focus, motion, and responsive rules available to the future Home without copying CSS blocks.

**Alternative considered:** A standalone CSS file would be workable, but Python-owned injection keeps the current deployment model simple and avoids a separate asset pipeline.

### 2. Layered glow background

**Decision:** Render two absolutely positioned background divs inside a scoped hero wrapper: an orange `#F97316` radial glow and a trust-blue `#1E3A8A` radial glow. Both use `filter: blur(80px-90px)`, low opacity, different pulse delays, and `z-index: 0`; content uses a higher stacking context.

**Rationale:** Controlled layers create depth while preserving the existing palette and avoiding a generic purple-blue gradient.

### 3. Local transparent illustrations

**Decision:** Read optional PNG/WebP files from `assets/`, convert bytes to base64 data URIs in Python, and render only assets that exist. Each illustration receives its own scoped class, drop shadow, duration, rotation, and delay. Missing files return no markup and never raise an exception.

**Rationale:** Reflex static assets should remain local and portable across deployments. Missing files must continue to be silent.

### 4. Glassmorphism treatment

**Decision:** Use a reusable `.glass-panel` class with translucent dark surface, `backdrop-filter: blur(16px)`, a 1px translucent border, large radius, and diffuse shadow. The assistance panel receives this class; future provider cards can reuse it.

**Rationale:** It creates visual continuity between the landing and future operational screens while keeping surfaces distinct from the background glow.

### 5. Typography, chips, and CTA

**Decision:** Keep the existing copy, set the hero headline around 3.2-3.5rem with weight 800 and negative tracking, highlight one keyword in orange, keep supporting text neutral with line-height 1.6, and give chips/CTA their own hover elevation. The CTA uses an orange gradient derived only from the emergency-orange family and a same-family shadow.

**Rationale:** Strong hierarchy makes the message scannable without introducing a new brand direction.

### 6. Motion and accessibility

**Decision:** Define independent `pulseGlow`, `floatIllustration`, and `lift` keyframes. A `prefers-reduced-motion: reduce` media query sets animation and transition durations to near-zero, removes transforms, and keeps all content visible.

**Rationale:** Motion supports depth but must never be necessary to understand or use the page.

### 7. Responsive layering

**Decision:** Keep glow and illustrations behind/around the hero on desktop; reduce illustration count, opacity, and size at mobile widths so text, CTA, and assistance panel remain primary. The wrapper clips overflow and preserves a stable content stacking order.

## Risks / Trade-offs

- **Backdrop blur support varies** → use a translucent solid fallback background behind the glass panel.
- **Large embedded images increase HTML size** → restrict to small local PNG/WebP assets and skip oversized files.
- **Glow may reduce contrast in an unusual theme** → keep opacity low, validate text contrast on the rendered surface, and retain opaque text colors.
- **CSS selectors can conflict with framework defaults** → scope custom classes and avoid broad global selectors.
- **Absent assets can reduce visual richness** → the base hero remains complete without illustrations, with no error state or broken-image icon.

## Migration Plan

1. Add the shared Python style module and optional `assets/` folder.
2. Move the landing hero CSS into the module and wrap the existing hero content with the scoped layered container.
3. Render available local illustrations and verify the silent fallback with an empty assets folder.
4. Validate desktop/mobile screenshots, keyboard focus, contrast, and reduced-motion mode.
5. Reuse the module from future Reflex screens when they are added.

## Open Questions

None. The scope explicitly excludes new dependencies and external renderers.
