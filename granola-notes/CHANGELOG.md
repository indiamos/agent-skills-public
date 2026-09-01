# Changelog

## 2026-08-31

- README Context section clarifies when to use this skill vs. Claude.AI connectors

## 2026-08-13

- Initial release
- Usage section now branches error handling by type: `429` retries, `401`/`403`/`404` halt and
  report to the user instead of retrying
- Rate-limit backoff given a concrete schedule (5s, doubling, 3 attempts) with an explicit halt
  condition instead of a bare "back off on 429"
- Add `find-note` command: client-side title substring search across `list-notes` pages
- Add transcript pagination: `getTranscript` and `get-transcript` CLI now accept `--cursor`
  and `--page-size` flags, matching the API's `?cursor=` / `?page_size=` query params
