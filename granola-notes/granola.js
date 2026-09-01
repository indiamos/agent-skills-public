#!/usr/bin/env node
// Thin wrapper around Granola's public REST API (https://docs.granola.ai).
// Auth: reads a personal API key from the GRANOLA_API_KEY environment variable.

const BASE_URL = "https://public-api.granola.ai/v1";

function apiKey() {
  const key = process.env.GRANOLA_API_KEY;
  if (!key) {
    console.error(
      "GRANOLA_API_KEY is not set. Generate a personal API key in Granola's " +
        "settings, then export it in your shell environment before running this script.",
    );
    process.exit(1);
  }
  return key;
}

async function request(path, params = {}) {
  const url = new URL(BASE_URL + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, v);
  }
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${apiKey()}` },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    console.error(`Granola API error ${res.status} ${res.statusText}: ${body}`);
    process.exit(1);
  }
  return res.json();
}

async function listNotes({ since, cursor } = {}) {
  return request("/notes", { created_after: since, cursor });
}

async function getNote(id, { transcript } = {}) {
  return request(`/notes/${encodeURIComponent(id)}`, {
    include: transcript ? "transcript" : undefined,
  });
}

async function getTranscript(id, { cursor, pageSize } = {}) {
  return request(`/notes/${encodeURIComponent(id)}/transcript`, {
    cursor,
    page_size: pageSize,
  });
}

function startOfTodayUTC() {
  const d = new Date();
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())).toISOString();
}

// Client-side title search: the /notes endpoint only supports created_after/cursor
// (no title or folder filter), so this pages through list-notes and filters locally.
// Folder can't be filtered this way — folder_membership is only returned by get-note,
// not list-notes, and fetching every note's detail to check it would be expensive.
async function findNotesByTitle({ title, since }) {
  const sinceResolved = since || startOfTodayUTC();
  const titleLower = title.toLowerCase();
  const matches = [];
  let cursor;
  do {
    const page = await listNotes({ since: sinceResolved, cursor });
    for (const n of page.notes) {
      if (n.title.toLowerCase().includes(titleLower)) matches.push(n);
    }
    cursor = page.hasMore ? page.cursor : null;
  } while (cursor);
  return matches;
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith("--")) {
        args[key] = next;
        i++;
      } else {
        args[key] = true;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

async function main() {
  const [command, ...rest] = process.argv.slice(2);
  const args = parseArgs(rest);
  let result;

  switch (command) {
    case "list-notes":
      result = await listNotes({ since: args.since, cursor: args.cursor });
      break;
    case "get-note":
      if (!args._[0]) {
        console.error("Usage: granola.js get-note <note_id> [--transcript]");
        process.exit(1);
      }
      result = await getNote(args._[0], { transcript: Boolean(args.transcript) });
      break;
    case "get-transcript":
      if (!args._[0]) {
        console.error("Usage: granola.js get-transcript <note_id> [--cursor <cursor>] [--page-size <n>]");
        process.exit(1);
      }
      result = await getTranscript(args._[0], {
        cursor: args.cursor,
        pageSize: args["page-size"] ? Number(args["page-size"]) : undefined,
      });
      break;
    case "find-note": {
      if (!args.title) {
        console.error(
          "Usage: granola.js find-note --title <substring> [--since <ISO8601>] [--transcript]",
        );
        process.exit(1);
      }
      const matches = await findNotesByTitle({ title: args.title, since: args.since });
      if (matches.length === 0) {
        console.error(
          `No notes matched title "${args.title}"` +
            (args.since ? ` since ${args.since}.` : " created today (UTC). Pass --since to widen the search."),
        );
        process.exit(1);
      }
      if (matches.length > 1) {
        console.error(
          `${matches.length} notes matched "${args.title}" — narrow --title or use get-note with one of these ids:`,
        );
        console.error(
          JSON.stringify(
            matches.map(({ id, title, created_at }) => ({ id, title, created_at })),
            null,
            2,
          ),
        );
        process.exit(1);
      }
      result = await getNote(matches[0].id, { transcript: Boolean(args.transcript) });
      break;
    }
    default:
      console.error(
        "Usage: granola.js <list-notes|get-note|get-transcript|find-note> [args]\n" +
          "  list-notes [--since <ISO8601>] [--cursor <cursor>]\n" +
          "  get-note <note_id> [--transcript]\n" +
          "  get-transcript <note_id> [--cursor <cursor>] [--page-size <n>]\n" +
          "  find-note --title <substring> [--since <ISO8601>] [--transcript]",
      );
      process.exit(1);
  }

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error(err.message || String(err));
  process.exit(1);
});
