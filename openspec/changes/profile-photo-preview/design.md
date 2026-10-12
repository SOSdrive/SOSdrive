## Context

See `proposal.md` for motivation and `specs/profile/photo-preview/spec.md` for observable behavior. The profile flow is implemented in Reflex in `sosdrive.py`. `AppState` already has separate profile-photo fields, a file-upload handler, and a save method that can send image content to Xano. The avatar currently renders `user_profile_photo`, while upload selection is wired through `rx.upload`; keep the existing profile screen and persistence flow.

## Goals / Non-Goals

**Goals:**
- Make file selection reliably invoke the existing Reflex upload event.
- Keep the selected image as a draft distinct from the persisted profile-photo URL.
- Reuse existing save and Xano multipart upload behavior, updating it only as needed to preserve the selected file's actual image type.
- Keep one avatar renderer consistent across profile selection and saved-photo fallback.

**Non-Goals:**
- Add React/Next.js components or a new frontend framework.
- Send or persist the image to Xano during selection.
- Change profile authorization, profile fields, or unrelated avatar presentation elsewhere.

## Decisions

### Keep the preview draft separate from persisted profile data

Use the existing Reflex profile state to retain selected image content as a temporary data URL. Render the avatar from the staged value first, then the persisted photo URL, then initials. Do not overwrite the persisted photo field merely to display a preview; commit/synchronize the staged value only after the profile save succeeds.

**Alternative considered:** Replace the persisted photo field immediately on selection. This is rejected because it conflates an unsaved edit with persisted profile data and complicates retry and failure behavior.

### Reuse the Reflex upload event rather than adding a React component

Wire the file picker's selection path to the existing upload handler and validate the selected content as an image before updating draft state. Keep file transfer to the Reflex backend separate from the Xano persistence request, which remains attached to the explicit save action.

**Alternative considered:** Add a standalone React hook and `URL.createObjectURL`. This is rejected because the project uses Python/Reflex, and the existing upload mechanism already provides file content to the profile state without adding a second frontend stack.

### Preserve image content metadata through save

When building the existing Xano upload payload, derive the filename and MIME type from the selected image instead of assuming PNG. Keep the persisted profile-photo URL as the fallback after the successful save response.

**Alternative considered:** Convert every accepted image to PNG. This is rejected because conversion adds processing and memory cost and is unnecessary for preview or upload.

## Risks / Trade-offs

- [The file picker may not invoke an upload handler wired only for drag-and-drop] → Exercise both picker selection and drag-and-drop; connect the correct Reflex selection event.
- [Malformed or non-image uploads could produce a broken avatar or upload payload] → Validate image MIME/content and reject invalid files without replacing the current preview.
- [Large image data URLs increase transient Reflex state size] → Keep the draft scoped to the active profile edit and clear or synchronize it after a successful save.

## Migration Plan

No database migration or dependency is required. If the UI or validation regresses, restore the prior profile upload handler and avatar conditional without changing persisted profile data.
