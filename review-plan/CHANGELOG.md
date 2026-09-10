# Changelog

## 2026-09-09

- Step 3/4 now build a full revised plan document (written to a `.reviewed` sibling file) instead of presenting isolated Replace/With snippets, so the original and revised plan can be compared side-by-side.
- Added check C2c: literal commit subject lines already drafted in a task step are now checked against the stated convention (ticket reference, ≤50 characters verified via `wc -c`, body when warranted) and rewritten if they violate it — previously a plan could state the correct convention and still ship a non-conforming message untouched.
- README's checklist item count had drifted stale twice (said "eleven-item" while the table already had 18 rows, pre-C2c); dropped the hardcoded count so it can't go stale again.

## 2026-09-03

- Initial release
