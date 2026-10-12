## 1. Xano upload endpoint and payload contract

- [x] 1.1 Normalize `nome_completo`, `cpf`, and `telefone` as primitive strings; verify formatted and empty values with focused unit tests.
- [x] 1.2 Add an authenticated Xano image-upload endpoint using a `file?` input and public image storage; validate its XanoScript and confirm the returned path is usable as a stable URL.

## 2. Profile save integration

- [x] 2.1 Reuse the staged profile image to upload multipart to the new endpoint, then send profile fields and the resulting URL as JSON; when unchanged, send the persisted URL or an empty string.
- [x] 2.2 Add focused tests for request field types, no-photo saves, upload failures, profile-save failures, and retry reuse of an uploaded URL.

## 3. Feedback and end-to-end verification

- [x] 3.1 Preserve the save loading/duplicate-submit behavior and success/error feedback; verify with state tests and Reflex compilation.
- [ ] 3.2 After push permission is enabled, preview and publish only to the confirmed SOS workspace branch, then verify upload and profile save end to end without changing unrelated profile values.
