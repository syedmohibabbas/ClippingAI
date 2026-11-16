# Platform access policy and integration notes

ClippingAI is intended to support YouTube, Facebook and Instagram where a lawful, supported access path exists.

## YouTube

- YouTube Data API can provide metadata and authorized account operations within granted scopes.
- API access does not provide a general right to download arbitrary public videos.
- Do not use unofficial downloaders or bypass platform restrictions.
- Support user uploads, creator-provided source files, or another explicitly authorized media delivery route.
- Live streams require an authorized ingest feed or supported account workflow.

## Facebook and Instagram

- Use Meta's official APIs and OAuth permissions.
- Availability depends on account type, app review, granted scopes, ownership / role and API product.
- Public visibility does not imply permission to download, edit or republish.
- Provide upload as a fallback for source files the user is entitled to process.
- Live stream processing requires a supported, authorized stream feed.

## User experience

When a pasted URL cannot be processed:
1. Explain the exact access limitation.
2. Offer an authorized upload route.
3. Preserve the project record without pretending that a download occurred.
4. Never claim a platform is fully supported until its adapter passes integration tests.

## Copyright

- Obtain permission, a suitable license, or a valid legal basis before processing / publishing.
- Fair use / fair dealing depends on jurisdiction and facts; there is no universal safe clip duration.
- Captions, crops, zooms, transitions and background music do not automatically make a use lawful.
- Risk flags are informational only and cannot guarantee no Content ID claim, takedown or strike.
