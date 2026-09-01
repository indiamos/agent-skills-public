import json
import pathlib
import subprocess
import sys
import tempfile

# Import the module under test
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import importlib
hoist = importlib.import_module("hoist-permissions")  # noqa: F401


def test_script_runs():
    result = subprocess.run(
        [sys.executable, str(__file__).replace("tests/test_hoist_permissions.py", "hoist-permissions.py"), "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0


def test_discover_finds_settings_files(tmp_path):
    # Create matching files
    (tmp_path / "proj-a" / ".claude").mkdir(parents=True)
    (tmp_path / "proj-a" / ".claude" / "settings.json").write_text("{}")
    (tmp_path / "proj-a" / ".claude" / "settings.local.json").write_text("{}")
    # Non-matching file — should be ignored
    (tmp_path / "proj-a" / ".claude" / "other.json").write_text("{}")

    found = hoist.discover([tmp_path])
    paths = {p.resolve() for p in found}
    assert (tmp_path / "proj-a" / ".claude" / "settings.json").resolve() in paths
    assert (tmp_path / "proj-a" / ".claude" / "settings.local.json").resolve() in paths
    assert (tmp_path / "proj-a" / ".claude" / "other.json").resolve() not in paths


def test_discover_excludes_root_and_hoisted(tmp_path):
    # Simulate ~/.claude being one of the roots
    dot_claude = tmp_path / ".claude"
    dot_claude.mkdir()
    settings = dot_claude / "settings.json"
    hoisted = dot_claude / "settings-hoisted.json"
    local = dot_claude / "settings.local.json"
    settings.write_text("{}")
    hoisted.write_text("{}")
    local.write_text("{}")

    # Patch EXCLUDE to use tmp paths
    original = hoist.EXCLUDE
    hoist.EXCLUDE = {settings.resolve(), hoisted.resolve()}
    try:
        found = hoist.discover([tmp_path])
        paths = {p.resolve() for p in found}
        assert settings.resolve() not in paths
        assert hoisted.resolve() not in paths
        assert local.resolve() in paths
    finally:
        hoist.EXCLUDE = original


def test_parse_file_valid_json(tmp_path):
    f = tmp_path / "settings.json"
    f.write_text('{"permissions": {"allow": ["Bash(*)"]}}')
    result, error = hoist.parse_file(f)
    assert error is None
    assert result == {"permissions": {"allow": ["Bash(*)"]}}


def test_parse_file_invalid_json(tmp_path):
    f = tmp_path / "settings.json"
    f.write_text("not json {{{")
    result, error = hoist.parse_file(f)
    assert result is None
    assert error is not None
    assert "not json" in error.lower() or "json" in error.lower()


def test_has_content_true_cases():
    assert hoist.has_content({"permissions": {"allow": ["Bash(*)"]}})
    assert hoist.has_content({"env": {"FOO": "bar"}})
    assert hoist.has_content({"someFlag": True})
    assert hoist.has_content({"someFlag": False})


def test_has_content_false_cases():
    assert not hoist.has_content({})
    assert not hoist.has_content({"permissions": {}})
    assert not hoist.has_content({"permissions": {"allow": [], "deny": []}})
    assert not hoist.has_content({"emptyString": ""})


def test_aggregate_dedupes_and_sorts():
    parsed_files = [
        {"permissions": {"allow": ["Bash(npm run:*)", "Bash(git:*)"]}},
        {"permissions": {"allow": ["Bash(git:*)", "mcp__foo__bar"]}},  # git:* is a dup
        {"permissions": {"deny": ["Bash(rm:*)"]}},
    ]
    allow, deny = hoist.aggregate(parsed_files)
    assert allow == ["Bash(git:*)", "Bash(npm run:*)", "mcp__foo__bar"]
    assert deny == ["Bash(rm:*)"]


def test_aggregate_case_sensitive_dedup():
    # Bash(*) and bash(*) differ in case — both kept
    parsed_files = [
        {"permissions": {"allow": ["Bash(*)", "bash(*)"]}},
    ]
    allow, deny = hoist.aggregate(parsed_files)
    assert "Bash(*)" in allow
    assert "bash(*)" in allow


def test_aggregate_case_insensitive_sort():
    parsed_files = [
        {"permissions": {"allow": ["mcp__z", "Bash(*)", "mcp__a"]}},
    ]
    allow, _ = hoist.aggregate(parsed_files)
    # Case-insensitive sort: Bash < mcp__a < mcp__z
    assert allow == ["Bash(*)", "mcp__a", "mcp__z"]


def test_aggregate_empty_input():
    allow, deny = hoist.aggregate([])
    assert allow == []
    assert deny == []


def test_aggregate_skips_missing_permissions_key():
    parsed_files = [{"env": {"FOO": "bar"}}]
    allow, deny = hoist.aggregate(parsed_files)
    assert allow == []
    assert deny == []


def test_write_hoisted_both_populated(tmp_path):
    out = tmp_path / "settings-hoisted.json"
    hoist.write_hoisted(["entry-a", "entry-b"], ["entry-c"], out)
    data = json.loads(out.read_text())
    assert data == {"permissions": {"allow": ["entry-a", "entry-b"], "deny": ["entry-c"]}}


def test_write_hoisted_omits_empty_deny(tmp_path):
    out = tmp_path / "settings-hoisted.json"
    hoist.write_hoisted(["entry-a"], [], out)
    data = json.loads(out.read_text())
    assert "deny" not in data["permissions"]
    assert data["permissions"]["allow"] == ["entry-a"]


def test_write_hoisted_omits_empty_allow(tmp_path):
    out = tmp_path / "settings-hoisted.json"
    hoist.write_hoisted([], ["entry-c"], out)
    data = json.loads(out.read_text())
    assert "allow" not in data["permissions"]
    assert data["permissions"]["deny"] == ["entry-c"]


def test_write_hoisted_both_empty(tmp_path):
    out = tmp_path / "settings-hoisted.json"
    hoist.write_hoisted([], [], out)
    data = json.loads(out.read_text())
    assert data == {"permissions": {}}


def test_write_hoisted_pretty_printed(tmp_path):
    out = tmp_path / "settings-hoisted.json"
    hoist.write_hoisted(["a", "b"], [], out)
    raw = out.read_text()
    # Each entry should be on its own line (indent=2)
    assert '    "a"' in raw
    assert '    "b"' in raw


def test_end_to_end(tmp_path):
    # Set up two fake project settings files
    proj_a = tmp_path / "proj-a" / ".claude"
    proj_a.mkdir(parents=True)
    (proj_a / "settings.local.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(npm run:*)", "Bash(git:*)"]}})
    )

    proj_b = tmp_path / "proj-b" / ".claude"
    proj_b.mkdir(parents=True)
    (proj_b / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(git:*)"], "deny": ["Bash(rm:*)"]}})
    )

    # Empty file — should not appear in the "has content" list
    proj_c = tmp_path / "proj-c" / ".claude"
    proj_c.mkdir(parents=True)
    (proj_c / "settings.json").write_text("{}")

    output = tmp_path / "settings-hoisted.json"

    result = subprocess.run(
        [
            sys.executable,
            str(pathlib.Path(__file__).parent.parent / "hoist-permissions.py"),
            "--roots", str(tmp_path),
            "--output", str(output),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr

    data = json.loads(output.read_text())
    assert data["permissions"]["allow"] == ["Bash(git:*)", "Bash(npm run:*)"]
    assert data["permissions"]["deny"] == ["Bash(rm:*)"]

    # Files with content reported; empty file not reported
    assert str((proj_a / "settings.local.json").resolve()) in result.stdout
    assert str((proj_b / "settings.json").resolve()) in result.stdout
    assert str((proj_c / "settings.json").resolve()) not in result.stdout
