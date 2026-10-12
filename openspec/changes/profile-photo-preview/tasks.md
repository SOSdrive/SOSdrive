## 1. Selection and draft image state

- [x] 1.1 Reuse the existing Reflex upload flow and ensure choosing a file in the picker invokes the profile upload handler; add focused tests for valid image data, unreadable/unsupported files, and preservation of the previous draft on rejection.
- [x] 1.2 Keep staged image data separate from the persisted profile photo and verify the avatar selects staged image, persisted photo, then initials in that priority order.

## 2. Avatar and save integration

- [x] 2.1 Apply circular cover styling to staged and persisted avatar images; verify both image sources render within the avatar without changing its dimensions.
- [x] 2.2 Reuse the existing profile save request to send the staged image only after save, preserving its MIME type and filename; test that a failed save retains the draft and a successful save synchronizes/clears it.

## 3. Verification

- [x] 3.1 Run focused profile-photo tests and Reflex compilation, then verify in the browser that selecting an image updates the avatar before saving and that the existing persisted-photo and initials fallbacks remain functional.
- [x] 3.2 Validate the change with `openspec validate profile-photo-preview --type change --strict`.
