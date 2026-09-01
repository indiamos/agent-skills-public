"""Tests for export-session.py — the export-full skill helper."""

import importlib.util
import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load the module from its file path (no package structure)
# ---------------------------------------------------------------------------

_SCRIPT = Path(__file__).parent.parent / "export-session.py"
spec = importlib.util.spec_from_file_location("export_session", _SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _jsonl(path: Path, records: list[dict]) -> Path:
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return path


@pytest.fixture
def jsonl_with_ts(tmp_path):
    return _jsonl(tmp_path / "session.jsonl", [
        {"type": "user", "timestamp": "2026-03-19T15:51:00.000Z",
         "message": {"role": "user", "content": "hello"}},
        {"type": "assistant", "timestamp": "2026-03-19T15:52:00.000Z",
         "message": {"role": "assistant", "content": [{"type": "text", "text": "hi"}]}},
    ])


@pytest.fixture
def jsonl_no_ts(tmp_path):
    return _jsonl(tmp_path / "no_ts.jsonl", [
        {"type": "user", "message": {"role": "user", "content": "hello"}},
    ])


# ---------------------------------------------------------------------------
# cmd_timestamp
# ---------------------------------------------------------------------------

class TestTimestamp:
    def test_returns_formatted_timestamp(self, jsonl_with_ts, capsys):
        rc = mod.cmd_timestamp(str(jsonl_with_ts))
        assert rc == 0
        out = capsys.readouterr().out.strip()
        # YYYY-MM-DD-HHMM → 15 chars, dashes at positions 4, 7, 10
        assert len(out) == 15
        assert out[4] == "-" and out[7] == "-" and out[10] == "-"

    def test_uses_first_record(self, tmp_path, capsys):
        """Timestamp comes from the FIRST record, not the latest."""
        p = _jsonl(tmp_path / "s.jsonl", [
            {"type": "user", "timestamp": "2026-01-01T10:00:00Z", "message": {}},
            {"type": "user", "timestamp": "2026-06-01T10:00:00Z", "message": {}},
        ])
        mod.cmd_timestamp(str(p))
        assert capsys.readouterr().out.strip().startswith("2026-01-01")

    def test_skips_blank_lines(self, tmp_path, capsys):
        p = tmp_path / "blanks.jsonl"
        p.write_text(
            "\n\n"
            + json.dumps({"type": "user", "timestamp": "2026-03-19T15:51:00Z", "message": {}})
            + "\n"
        )
        assert mod.cmd_timestamp(str(p)) == 0

    def test_skips_invalid_json_lines(self, tmp_path, capsys):
        p = tmp_path / "bad.jsonl"
        p.write_text(
            "not json\n"
            + json.dumps({"type": "user", "timestamp": "2026-03-19T15:51:00Z", "message": {}})
            + "\n"
        )
        assert mod.cmd_timestamp(str(p)) == 0

    def test_no_timestamp_returns_1(self, jsonl_no_ts):
        assert mod.cmd_timestamp(str(jsonl_no_ts)) == 1

    def test_empty_file_returns_1(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("")
        assert mod.cmd_timestamp(str(p)) == 1

    def test_missing_file_returns_1(self, tmp_path):
        assert mod.cmd_timestamp(str(tmp_path / "nope.jsonl")) == 1


# ---------------------------------------------------------------------------
# cmd_finalize
# ---------------------------------------------------------------------------

class TestFinalize:
    def test_appends_summary_line(self, tmp_path, capsys):
        p = tmp_path / "out.md"
        p.write_text("line1\nline2\n")
        rc = mod.cmd_finalize(str(p), ".ai-context/foo/2026-03-19-topic.md", "A great conversation.")
        assert rc == 0
        last = p.read_text().splitlines()[-1]
        assert last == "Exported to .ai-context/foo/2026-03-19-topic.md — 2 lines, 1K. A great conversation."

    def test_prints_summary_to_stdout(self, tmp_path, capsys):
        p = tmp_path / "out.md"
        p.write_text("content\n")
        mod.cmd_finalize(str(p), "rel/path.md", "Description.")
        out = capsys.readouterr().out.strip()
        assert out.startswith("Exported to rel/path.md —")
        assert out.endswith("Description.")

    def test_line_count_is_pre_trim(self, tmp_path, capsys):
        """Reported N reflects the file before trimming/appending."""
        p = tmp_path / "out.md"
        # 3 real lines + 2 trailing blank lines
        p.write_text("a\nb\nc\n\n\n")
        mod.cmd_finalize(str(p), "r.md", "D.")
        out = capsys.readouterr().out
        n = int(out.split("—")[1].split("lines")[0].strip())
        assert n == 5

    def test_strips_trailing_blank_lines(self, tmp_path):
        p = tmp_path / "out.md"
        p.write_text("content\n\n\n")
        mod.cmd_finalize(str(p), "r.md", "D.")
        lines = p.read_text().splitlines()
        assert lines[-1] == "Exported to r.md — 3 lines, 1K. D."

    def test_strips_trailing_md_tool_opener(self, tmp_path):
        p = tmp_path / "out.md"
        p.write_text("real content\n\n**`Bash(python3 export-session.py ...)`**\n")
        mod.cmd_finalize(str(p), "r.md", "D.")
        assert "**`Bash" not in p.read_text()

    def test_strips_trailing_md_tool_closer(self, tmp_path):
        p = tmp_path / "out.md"
        p.write_text("real content\n**`Bash(a b c)`**\n")
        mod.cmd_finalize(str(p), "r.md", "D.")
        assert ")`**" not in p.read_text()

    def test_strips_trailing_txt_glyph(self, tmp_path):
        p = tmp_path / "out.txt"
        p.write_text("real content\n\n⏺ Bash(something)\n")
        mod.cmd_finalize(str(p), "r.md", "D.")
        assert "⏺" not in p.read_text()

    def test_strips_trailing_bash_comment(self, tmp_path):
        p = tmp_path / "out.txt"
        p.write_text("real content\n  # Run the conversion\n")
        mod.cmd_finalize(str(p), "r.md", "D.")
        assert "  # Run" not in p.read_text()

    def test_preserves_non_trailing_content(self, tmp_path):
        p = tmp_path / "out.md"
        p.write_text("**`NotAtEnd`**\nreal content\n")
        mod.cmd_finalize(str(p), "r.md", "D.")
        assert "**`NotAtEnd`**" in p.read_text()

    def test_missing_file_returns_1(self, tmp_path):
        assert mod.cmd_finalize(str(tmp_path / "nope.md"), "r.md", "D.") == 1


# ---------------------------------------------------------------------------
# _resolve_output_dir
# ---------------------------------------------------------------------------

def _write_settings(path: Path, output_dir: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"env": {"EXPORT_FULL_OUTPUT_DIR": output_dir}}))


class TestResolveOutputDir:
    def test_no_settings_returns_empty(self, tmp_path):
        assert mod._resolve_output_dir(str(tmp_path), home=str(tmp_path / "home")) == ""

    def test_global_settings_only(self, tmp_path):
        home = tmp_path / "home"
        _write_settings(home / ".claude" / "settings.json", "global/conversations")
        assert mod._resolve_output_dir(str(tmp_path / "repo"), home=str(home)) == "global/conversations"

    def test_project_settings_overrides_global(self, tmp_path):
        home = tmp_path / "home"
        repo = tmp_path / "repo"
        _write_settings(home / ".claude" / "settings.json", "global/conversations")
        _write_settings(repo / ".claude" / "settings.json", "project/conversations")
        assert mod._resolve_output_dir(str(repo), home=str(home)) == "project/conversations"

    def test_project_local_overrides_project(self, tmp_path):
        home = tmp_path / "home"
        repo = tmp_path / "repo"
        _write_settings(home / ".claude" / "settings.json", "global/conversations")
        _write_settings(repo / ".claude" / "settings.json", "project/conversations")
        _write_settings(repo / ".claude" / "settings.local.json", "local/conversations")
        assert mod._resolve_output_dir(str(repo), home=str(home)) == "local/conversations"

    def test_project_settings_without_global(self, tmp_path):
        home = tmp_path / "home"
        repo = tmp_path / "repo"
        _write_settings(repo / ".claude" / "settings.json", "project/conversations")
        assert mod._resolve_output_dir(str(repo), home=str(home)) == "project/conversations"

    def test_missing_key_in_settings_file(self, tmp_path):
        home = tmp_path / "home"
        repo = tmp_path / "repo"
        settings = home / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({"env": {"OTHER_KEY": "value"}}))
        assert mod._resolve_output_dir(str(repo), home=str(home)) == ""

    def test_malformed_json_skipped(self, tmp_path):
        home = tmp_path / "home"
        repo = tmp_path / "repo"
        bad = home / ".claude" / "settings.json"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("not json {{{")
        _write_settings(repo / ".claude" / "settings.json", "project/conversations")
        assert mod._resolve_output_dir(str(repo), home=str(home)) == "project/conversations"

    def test_env_key_missing_entirely(self, tmp_path):
        home = tmp_path / "home"
        repo = tmp_path / "repo"
        settings = home / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({"model": "sonnet"}))
        assert mod._resolve_output_dir(str(repo), home=str(home)) == ""


# ---------------------------------------------------------------------------
# cmd_find_current (settings resolution)
# ---------------------------------------------------------------------------

def _make_jsonl(session_dir: Path, ts: str = "2026-05-26T20:09:00Z") -> Path:
    session_dir.mkdir(parents=True, exist_ok=True)
    p = session_dir / "abc123.jsonl"
    p.write_text(json.dumps({"type": "user", "timestamp": ts, "message": {}}) + "\n")
    return p


class TestFindCurrentSettingsResolution:
    def test_output_dir_from_project_settings(self, tmp_path, monkeypatch):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        home = tmp_path / "home"
        project_dir = str(repo).replace("/", "-").replace(".", "-").replace("_", "-")
        _make_jsonl(home / ".claude" / "projects" / project_dir)
        _write_settings(home / ".claude" / "settings.json", "global/conversations")
        _write_settings(repo / ".claude" / "settings.json", "project/conversations")

        monkeypatch.setenv("HOME", str(home))
        lines = {}
        captured = []
        monkeypatch.setattr("builtins.print", lambda *a, **kw: captured.append(a[0] if a else ""))

        rc = mod.cmd_find_current(cwd=str(repo), home=str(home))
        assert rc == 0
        output_line = next(l for l in captured if l.startswith("OUTPUT_DIR="))
        assert output_line == "OUTPUT_DIR=project/conversations"

    def test_output_dir_falls_back_to_global(self, tmp_path, monkeypatch):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        home = tmp_path / "home"
        project_dir = str(repo).replace("/", "-").replace(".", "-").replace("_", "-")
        _make_jsonl(home / ".claude" / "projects" / project_dir)
        _write_settings(home / ".claude" / "settings.json", "global/conversations")

        captured = []
        monkeypatch.setattr("builtins.print", lambda *a, **kw: captured.append(a[0] if a else ""))

        rc = mod.cmd_find_current(cwd=str(repo), home=str(home))
        assert rc == 0
        output_line = next(l for l in captured if l.startswith("OUTPUT_DIR="))
        assert output_line == "OUTPUT_DIR=global/conversations"

    def test_output_dir_empty_when_no_settings(self, tmp_path, monkeypatch):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        home = tmp_path / "home"
        project_dir = str(repo).replace("/", "-").replace(".", "-").replace("_", "-")
        _make_jsonl(home / ".claude" / "projects" / project_dir)

        captured = []
        monkeypatch.setattr("builtins.print", lambda *a, **kw: captured.append(a[0] if a else ""))

        rc = mod.cmd_find_current(cwd=str(repo), home=str(home))
        assert rc == 0
        output_line = next(l for l in captured if l.startswith("OUTPUT_DIR="))
        assert output_line == "OUTPUT_DIR="


# ---------------------------------------------------------------------------
# _human_size
# ---------------------------------------------------------------------------

class TestHumanSize:
    def test_zero_bytes_returns_1k(self):
        assert mod._human_size(0) == "1K"

    def test_under_1kb(self):
        assert mod._human_size(500) == "1K"

    def test_exact_1kb(self):
        assert mod._human_size(1024) == "1K"

    def test_8kb(self):
        assert mod._human_size(8192) == "8K"

    def test_megabyte(self):
        assert mod._human_size(1024 * 1024) == "1M"

    def test_rounds_up(self):
        # 1025 bytes → 2K (ceil division)
        assert mod._human_size(1025) == "2K"
