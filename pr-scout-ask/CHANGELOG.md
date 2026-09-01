# Changelog

## 2026-05-05

- Review file is now the sole authoritative source for which issues to convert — issues present in earlier conversation context but absent from the file are explicitly excluded

## 2026-04-24

- Step 1.5 added: verifies each issue's referenced code still exists in the current PR diff before reframing; flags issues whose file was removed or whose line numbers may have shifted

## 2026-04-16

- Issues now classified as line-specific or cross-location before reframing; cross-location issues attach to the more relevant passage and reference the other by name and line range
- Blank line added between question and evidence portions of a comment when both are present

## 2026-04-01

- Initial release (renamed from `pr-scout.ask`)
