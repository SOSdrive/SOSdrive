## Context

See `proposal.md` for motivation and `specs/web/login-background-video/spec.md` for observable behavior. The login page is implemented in Reflex in `sosdrive.py`, and shared CSS-in-Python rules are in `styles.py`. A local MP4 already exists under `assets/`. The current login component is centered in the viewport; this change must place the card on the left as requested while leaving the authentication state and form actions intact.

## Goals / Non-Goals

**Goals:**
- Add a decorative video and contrast overlay to the login route only.
- Keep the video source easy to replace and preserve a non-video background.
- Keep the existing login form, navigation, and authentication behavior usable.
- Align the responsive login card to the left.

**Non-Goals:**
- Change authentication, session handling, API calls, or account navigation.
- Add a new video asset, external media service, frontend framework, or runtime dependency.
- Apply the video to the landing page or other authenticated pages.

## Decisions

### Use the existing local video with a single source setting

Define the source in one clearly named setting in the login implementation and initialize it to the MP4 already present in `assets/`. This reuses a checked-in asset while allowing future replacement without changing the page structure. An externally hosted source or an environment-based setting is unnecessary for the current single-asset use case.

### Build the background as layered decorative elements

Place a semantic video element and a separate overlay behind the login content. Configure the video for autoplay, looping, muted playback, and inline mobile playback; size it to the viewport with cover behavior. Use a local static poster as the fallback frame when video playback cannot begin, with a solid CSS background as the final fallback if both media resources fail. Use explicit nonnegative stacking levels for the video, overlay, and content rather than a negative stacking level, so the layers stay behind the form without falling behind the page canvas. Disable pointer events on the decorative layers.

### Reuse the login component and shared styles

Extend the existing `login_screen` and shared CSS rules rather than adding a separate route or duplicating the login form. Make the outer login layout occupy the viewport and position the unchanged card on the left with responsive spacing. Give the form content a higher stacking level than the video and overlay. No backend validation or authorization behavior changes.

## Risks / Trade-offs

- [Some browsers or device settings can prevent autoplay] → Keep the video muted and inline, and ensure the fallback background and form remain usable without playback.
- [Video may compete with form readability or increase visual distraction] → Add a translucent dark overlay, retain the solid card, and verify contrast across the viewport.
- [A replacement URL may be invalid or unavailable] → Keep a CSS background fallback and do not make login interactions depend on media loading.

## Migration Plan

No data, API, or dependency migration is needed. The change is limited to the login presentation and its styles. Roll back by removing the login background layers and their styles; the existing login form and authentication state remain unchanged.

## Verification

- Validate that the rendered video has autoplay, loop, muted, and plays-inline behavior and fills the viewport proportionally.
- Verify z-order and pointer interaction for the video, overlay, and login card.
- Exercise login inputs and all login-page actions on desktop and mobile viewport sizes.
- Test an unavailable video source and a browser state where autoplay is blocked; verify the fallback and form remain usable.
