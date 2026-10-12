## Context

See `proposal.md` for the motivation and `specs/web/runtime-stability/spec.md` for observable requirements. The app is written in Python with Reflex 0.8.28 and builds a generated React frontend. `sosdrive.py` currently supplies `rx.html` fragments as `head_components`; the browser reports an `rx-Html` `<div>` nested inside `<head>`. The same app loads Leaflet scripts and initializes map helpers. Reflex's development CLI accepts separate frontend and backend ports.

## Goals / Non-Goals

**Goals:**
- Keep the document head semantically valid and eliminate the invalid React hydration tree.
- Preserve Leaflet maps by loading their stylesheet and script through supported Reflex resource APIs and initializing map helpers after the dependency is present.
- Ensure the generated client connects to the currently configured frontend/backend addresses rather than stale development ports.
- Keep the fix in the Python/Reflex stack and avoid terminating processes that do not belong to this app.

**Non-Goals:**
- Add Next.js or React source components, or add a `'use client'` directive to Python code.
- Change map behavior, application routes, authentication, or domain data.
- Hardcode a developer-specific host or port into generated frontend code.

## Decisions

### Use semantic Reflex head and script resources

Replace `rx.html` fragments in `head_components` with supported stylesheet/resource or semantic tag components so Reflex does not wrap raw head markup in a body-level `<div>`. Keep executable map initialization separate from stylesheet loading and ensure Leaflet is present before map helpers execute. Browser-only reads or initialization must remain outside the initial server-rendered tree.

**Alternative considered:** Keep the current fragments and suppress hydration warnings. This is rejected because it hides invalid document structure and does not guarantee scripts execute reliably.

### Derive development socket addresses from the active Reflex run configuration

Use Reflex's supported CLI/configuration path for frontend and backend hosts/ports. Avoid adding a fixed `localhost:3000` or `localhost:8000` to app code. Validate actual HMR and app WebSocket targets against the ports passed to the running app.

**Alternative considered:** Hardcode WebSocket URLs in custom JavaScript. This is rejected because it breaks when a developer chooses different ports or accesses the frontend through another host.

### Verify port ownership before restarting services

Check active listeners and their owning processes before starting or stopping a local service. Start the app on explicitly selected free ports and verify both HTTP readiness and browser WebSocket behavior; do not kill unrelated processes just to free a conventional port.

**Alternative considered:** Terminate whichever process owns a default port. This is rejected because the workstation may be shared and that process may belong to another project.

## Risks / Trade-offs

- [Leaflet may load after map initialization] → Gate map helper initialization on the script's load/readiness event and verify existing map routes.
- [Reflex-generated development URLs can differ between frontend and backend hosts] → Validate compiled/runtime URLs for both sockets using the active CLI arguments; do not infer readiness from compilation alone.
- [Third-party libraries or browser extensions can still log unrelated warnings] → Verify the actual document structure and distinguish app-originating hydration/socket errors from unrelated console messages.

## Migration Plan

No persistent data or dependency migration is required. Roll back by restoring the existing app resource registration and development launch configuration; no domain data is touched.
