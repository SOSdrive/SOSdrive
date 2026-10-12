## Context

See `proposal.md` for motivation and `specs/profile/profile-save/spec.md` for the request and user-visible behavior. The authenticated Xano profile endpoint accepts `foto_perfil` as text and its PUT writes that input directly. It does not accept a file object, and omitting the optional input does not preserve the existing field.

The selected SOS workspace has matching profile endpoint definitions and no existing photo-upload endpoint. Xano supports authenticated `file?` inputs and public image storage through `storage.create_image`.

## Goals / Non-Goals

**Goals:**
- Normalize profile text fields at the Python request boundary.
- Upload a selected JPEG/PNG through a distinct authenticated Xano endpoint.
- Save the returned stable public image URL as a string through the existing profile POST/PUT endpoint.
- Preserve an existing photo URL when no new image is selected.
- Reuse the current Reflex picker, staged image, save action, and profile endpoints.

**Non-Goals:**
- Send multipart file data to the text-typed profile endpoint.
- Change profile field names, user authorization, or database schema.
- Change the workspace live branch or upload unrelated Xano resources.

## Decisions

### Separate file upload from profile persistence

Add an authenticated `POST /user_profile/photo` endpoint with an optional `file? foto_perfil` input. Store the validated image with `storage.create_image` using public access and the original filename, then return the stored path. The Reflex backend sends the selected bytes to this endpoint as multipart data and combines the returned path with the Xano instance origin to form the stable public URL.

**Alternative considered:** Send the file object as multipart data to `/user_profile`. Rejected because the deployed profile endpoint declares `foto_perfil` as text, not file.

**Alternative considered:** Store the full Base64 data URL in the text column. Rejected because it increases database and profile-response size and the user chose a separate upload endpoint.

### Save profile fields as a JSON object of strings

The profile request uses the existing `nome_completo`, `cpf`, and `telefone` names, normalized to strings. `foto_perfil` is always a string: use the uploaded URL after a successful upload, the persisted URL when unchanged, or `""` when no photo exists. This is required because the Xano PUT writes `$input.foto_perfil` unconditionally.

### Retain upload result across a failed profile save

After upload succeeds, retain the resulting URL alongside the staged image until the profile save succeeds. If the profile update fails, a retry reuses that URL instead of uploading a duplicate. Changing the selected image clears the prior upload result.

### Keep deployment scoped to the SOS workspace

Add the XanoScript source under the repository's existing profile API source layout. Before publishing, confirm the target branch and preview the workspace push; do not change which branch is live. The currently selected workspace reports `allow_push: false`, so deployment remains gated until that permission is enabled.

## Risks / Trade-offs

- [Public image URLs are accessible to anyone who obtains the link] → Use public access only for profile-avatar images, as explicitly selected; never include credentials or private profile fields in the upload response.
- [Profile persistence can fail after the image is uploaded, leaving an unused asset] → Retain the upload URL for retries and report the profile error; the Xano storage flow has no transactional rollback in this change.
- [The wrong workspace or branch could be changed] → Use the verified SOS workspace, inspect the target branch, run a dry-run, and never switch the live branch.
- [Workspace push is currently disabled] → Keep deployment verification pending until the workspace owner enables the existing push permission; do not bypass it.

## Migration Plan

No database migration is needed because `foto_perfil` remains text. Deploy the authenticated upload endpoint to the intended SOS workspace branch before relying on the new frontend call. Rollback by restoring the prior client flow and removing the new endpoint through the normal reviewed Xano workspace workflow; already uploaded public images may require separate cleanup.
