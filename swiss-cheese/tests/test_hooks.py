"""Unit tests for swiss-cheese gate_check hook (read-only version)."""
import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from gate_check import (
    GateStatus,
    GateResult,
    StalenessResult,
    ValidationReport,
    LAYERS,
    get_project_dir,
    get_current_git_hash,
    read_report,
    check_staleness,
    get_first_failing_layer,
    format_staleness_warning,
    format_status_message,
    main,
)


class TestGateStatus:
    """Test GateStatus enum."""

    def test_status_values(self):
        """GateStatus has expected values."""
        assert GateStatus.PASS.value == "PASS"
        assert GateStatus.FAIL.value == "FAIL"
        assert GateStatus.NOT_RUN.value == "NOT_RUN"


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_immutable(self):
        """GateResult is frozen (immutable)."""
        result = GateResult(layer=1, name="requirements", status=GateStatus.PASS)
        with pytest.raises(AttributeError):
            result.status = GateStatus.FAIL

    def test_gate_result_with_message(self):
        """GateResult stores optional message."""
        result = GateResult(
            layer=1,
            name="requirements",
            status=GateStatus.FAIL,
            message="design.md not found",
        )
        assert result.message == "design.md not found"

    def test_gate_result_default_message(self):
        """GateResult message defaults to None."""
        result = GateResult(layer=1, name="requirements", status=GateStatus.PASS)
        assert result.message is None


class TestStalenessResult:
    """Test StalenessResult dataclass."""

    def test_staleness_result_immutable(self):
        """StalenessResult is frozen (immutable)."""
        result = StalenessResult(is_stale=True, report_hash="abc1234", current_hash="def5678")
        with pytest.raises(AttributeError):
            result.is_stale = False

    def test_staleness_result_fields(self):
        """StalenessResult stores all fields."""
        result = StalenessResult(is_stale=True, report_hash="abc1234", current_hash="def5678")
        assert result.is_stale is True
        assert result.report_hash == "abc1234"
        assert result.current_hash == "def5678"


class TestLayers:
    """Test LAYERS constant."""

    def test_four_layers_defined(self):
        """LAYERS has 4 verification layers."""
        assert len(LAYERS) == 4

    def test_layer_structure(self):
        """Each layer has (name, make_target) tuple."""
        for layer_num, (name, target) in LAYERS.items():
            assert isinstance(layer_num, int)
            assert 1 <= layer_num <= 4
            assert isinstance(name, str)
            assert isinstance(target, str)
            assert target.startswith("validate-")

    def test_expected_layers(self):
        """LAYERS contains expected layer names."""
        layer_names = [name for name, _ in LAYERS.values()]
        assert "requirements" in layer_names
        assert "tdd" in layer_names
        assert "implementation" in layer_names
        assert "verify" in layer_names


class TestGetProjectDir:
    """Test get_project_dir function."""

    def test_uses_env_var(self):
        """Uses CLAUDE_PROJECT_DIR if set."""
        with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": "/custom/dir"}):
            result = get_project_dir()
            assert result == Path("/custom/dir")

    def test_defaults_to_cwd(self):
        """Defaults to current working directory."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("gate_check.Path.cwd", return_value=Path("/some/cwd")):
                result = get_project_dir()
                assert result == Path("/some/cwd")


class TestGetCurrentGitHash:
    """Test get_current_git_hash function."""

    def test_returns_hash_in_git_repo(self):
        """Returns git hash in a git repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import subprocess
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
            Path(tmpdir, "test.txt").write_text("test")
            subprocess.run(["git", "add", "test.txt"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "test"], cwd=tmpdir, capture_output=True)

            result = get_current_git_hash(Path(tmpdir))
            assert len(result) == 40  # Full SHA-1 hash

    def test_returns_empty_string_non_git_dir(self):
        """Returns empty string for non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_current_git_hash(Path(tmpdir))
            assert result == ""


class TestReadReport:
    """Test read_report function."""

    def test_read_valid_report(self):
        """Reads valid report JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir) / ".swiss-cheese" / "reports"
            report_dir.mkdir(parents=True)
            report_path = report_dir / "validation_report.json"
            report_path.write_text(json.dumps({
                "meta": {
                    "git_hash": "abc1234567890",
                    "git_hash_short": "abc1234",
                    "timestamp": "2026-02-03T12:00:00Z",
                },
                "layers": {
                    "requirements": {"status": "PASS", "checked_at": "2026-02-03T12:00:00Z"},
                    "tdd": {"status": "FAIL", "message": "Tests don't compile"},
                },
            }))

            result = read_report(report_path)
            assert result is not None
            assert result.git_hash == "abc1234567890"
            assert result.git_hash_short == "abc1234"
            assert result.layers["requirements"]["status"] == "PASS"
            assert result.layers["tdd"]["status"] == "FAIL"

    def test_read_nonexistent_report(self):
        """Returns None for nonexistent report."""
        result = read_report(Path("/nonexistent/path/report.json"))
        assert result is None

    def test_read_invalid_json(self):
        """Returns None for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report_path.write_text("not valid json {{{")

            result = read_report(report_path)
            assert result is None

    def test_read_report_with_optional_fields(self):
        """Reads report with optional coverage/tests/traceability."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report_path.write_text(json.dumps({
                "meta": {
                    "git_hash": "abc1234",
                    "git_hash_short": "abc1234",
                    "timestamp": "2026-02-03T12:00:00Z",
                },
                "layers": {},
                "coverage": {"line_percent": 75.5},
                "tests": {"total": 10, "passed": 10},
                "traceability": {"requirements_count": 5},
            }))

            result = read_report(report_path)
            assert result is not None
            assert result.coverage == {"line_percent": 75.5}
            assert result.tests == {"total": 10, "passed": 10}
            assert result.traceability == {"requirements_count": 5}


class TestCheckStaleness:
    """Test check_staleness function."""

    def test_same_hash_not_stale(self):
        """Same hash = not stale."""
        result = check_staleness("abc1234567890", "abc1234567890")
        assert result.is_stale is False
        assert result.report_hash == "abc1234"
        assert result.current_hash == "abc1234"

    def test_different_hash_is_stale(self):
        """Different hash = stale."""
        result = check_staleness("abc1234567890", "def5678901234")
        assert result.is_stale is True
        assert result.report_hash == "abc1234"
        assert result.current_hash == "def5678"

    def test_empty_report_hash_not_stale(self):
        """Empty report hash = not stale (no report)."""
        result = check_staleness("", "abc1234")
        assert result.is_stale is False

    def test_empty_current_hash_not_stale(self):
        """Empty current hash = not stale (not a git repo)."""
        result = check_staleness("abc1234", "")
        assert result.is_stale is False

    def test_uses_short_hash_for_comparison(self):
        """Uses first 7 chars for comparison."""
        # Same first 7 chars but different full hash
        result = check_staleness("abc1234XXXXXXX", "abc1234YYYYYYY")
        assert result.is_stale is False


class TestGetFirstFailingLayer:
    """Test get_first_failing_layer function."""

    def test_all_pass_returns_none(self):
        """Returns None when all layers pass."""
        report = ValidationReport(
            git_hash="abc",
            git_hash_short="abc",
            timestamp="",
            layers={
                "requirements": {"status": "PASS"},
                "tdd": {"status": "PASS"},
                "implementation": {"status": "PASS"},
                "verify": {"status": "PASS"},
            },
        )
        assert get_first_failing_layer(report) is None

    def test_first_failure_detected(self):
        """Returns first failing layer."""
        report = ValidationReport(
            git_hash="abc",
            git_hash_short="abc",
            timestamp="",
            layers={
                "requirements": {"status": "PASS"},
                "tdd": {"status": "FAIL", "message": "Tests don't compile"},
                "implementation": {"status": "NOT_RUN"},
                "verify": {"status": "NOT_RUN"},
            },
        )
        result = get_first_failing_layer(report)
        assert result is not None
        assert result[0] == 2  # Layer number
        assert result[1] == "tdd"  # Layer name
        assert result[2] == "Tests don't compile"

    def test_not_run_not_treated_as_failure(self):
        """NOT_RUN is not treated as failure."""
        report = ValidationReport(
            git_hash="abc",
            git_hash_short="abc",
            timestamp="",
            layers={
                "requirements": {"status": "PASS"},
                "tdd": {"status": "NOT_RUN"},
                "implementation": {"status": "NOT_RUN"},
                "verify": {"status": "NOT_RUN"},
            },
        )
        assert get_first_failing_layer(report) is None

    def test_uses_output_if_no_message(self):
        """Uses output field if message is empty."""
        report = ValidationReport(
            git_hash="abc",
            git_hash_short="abc",
            timestamp="",
            layers={
                "requirements": {"status": "FAIL", "output": "error output"},
            },
        )
        result = get_first_failing_layer(report)
        assert result is not None
        assert result[2] == "error output"


class TestFormatStalenessWarning:
    """Test format_staleness_warning function."""

    def test_format_warning(self):
        """Formats staleness warning with hashes."""
        staleness = StalenessResult(is_stale=True, report_hash="abc1234", current_hash="def5678")
        result = format_staleness_warning(staleness)
        assert "abc1234" in result
        assert "def5678" in result
        assert "stale" in result.lower()
        assert "/swiss-cheese:generate-reports" in result


class TestFormatStatusMessage:
    """Test format_status_message function."""

    def test_format_pass(self):
        """Format passing gate status."""
        result = GateResult(layer=1, name="requirements", status=GateStatus.PASS)
        message = format_status_message(result, 1)
        assert "Swiss Cheese Gate Status" in message
        assert "1 - requirements" in message
        assert "PASS" in message

    def test_format_fail_includes_output(self):
        """Format failing gate includes output."""
        result = GateResult(
            layer=1,
            name="requirements",
            status=GateStatus.FAIL,
            message="ERROR: design.md not found",
        )
        message = format_status_message(result, 1)
        assert "FAIL" in message
        assert "design.md not found" in message
        assert "validate-requirements" in message

    def test_format_not_run_includes_note(self):
        """Format NOT_RUN includes note."""
        result = GateResult(
            layer=1,
            name="requirements",
            status=GateStatus.NOT_RUN,
            message="No Makefile",
        )
        message = format_status_message(result, 1)
        assert "NOT_RUN" in message
        assert "No Makefile" in message

    def test_format_with_staleness_warning(self):
        """Format includes staleness warning when stale."""
        result = GateResult(layer=1, name="requirements", status=GateStatus.PASS)
        staleness = StalenessResult(is_stale=True, report_hash="abc1234", current_hash="def5678")
        message = format_status_message(result, 1, staleness)
        assert "stale" in message.lower()
        assert "abc1234" in message

    def test_format_no_staleness_when_fresh(self):
        """Format omits staleness warning when fresh."""
        result = GateResult(layer=1, name="requirements", status=GateStatus.PASS)
        staleness = StalenessResult(is_stale=False, report_hash="abc1234", current_hash="abc1234")
        message = format_status_message(result, 1, staleness)
        assert "stale" not in message.lower()


class TestMainReadOnly:
    """Test main function (hook entry point) - read-only behavior."""

    def test_main_no_report_continues_silently(self):
        """Continues silently when no report file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        assert "systemMessage" not in output

    def test_main_all_pass_continues_silently(self):
        """Continues silently when all gates pass and not stale."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create report directory
            report_dir = Path(tmpdir) / ".swiss-cheese" / "reports"
            report_dir.mkdir(parents=True)
            report_path = report_dir / "validation_report.json"

            # Create git repo with known hash
            import subprocess
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
            Path(tmpdir, "test.txt").write_text("test")
            subprocess.run(["git", "add", "test.txt"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "test"], cwd=tmpdir, capture_output=True)

            # Get current hash
            result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True)
            current_hash = result.stdout.strip()

            # Write report with same hash
            report_path.write_text(json.dumps({
                "meta": {
                    "git_hash": current_hash,
                    "git_hash_short": current_hash[:7],
                    "timestamp": "2026-02-03T12:00:00Z",
                },
                "layers": {
                    "requirements": {"status": "PASS"},
                    "tdd": {"status": "PASS"},
                    "implementation": {"status": "PASS"},
                    "verify": {"status": "PASS"},
                },
            }))

            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        assert "systemMessage" not in output

    def test_main_stale_report_shows_warning(self):
        """Shows staleness warning when report hash differs from HEAD."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create report directory
            report_dir = Path(tmpdir) / ".swiss-cheese" / "reports"
            report_dir.mkdir(parents=True)
            report_path = report_dir / "validation_report.json"

            # Create git repo
            import subprocess
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
            Path(tmpdir, "test.txt").write_text("test")
            subprocess.run(["git", "add", "test.txt"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "test"], cwd=tmpdir, capture_output=True)

            # Write report with different hash
            report_path.write_text(json.dumps({
                "meta": {
                    "git_hash": "0000000000000000000000000000000000000000",
                    "git_hash_short": "0000000",
                    "timestamp": "2026-02-03T12:00:00Z",
                },
                "layers": {
                    "requirements": {"status": "PASS"},
                    "tdd": {"status": "PASS"},
                    "implementation": {"status": "PASS"},
                    "verify": {"status": "PASS"},
                },
            }))

            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        assert "systemMessage" in output
                        assert "stale" in output["systemMessage"].lower()

    def test_main_gate_fail_shows_message(self):
        """Shows system message when gate fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create report with failure
            report_dir = Path(tmpdir) / ".swiss-cheese" / "reports"
            report_dir.mkdir(parents=True)
            report_path = report_dir / "validation_report.json"
            report_path.write_text(json.dumps({
                "meta": {
                    "git_hash": "abc1234567890",
                    "git_hash_short": "abc1234",
                    "timestamp": "2026-02-03T12:00:00Z",
                },
                "layers": {
                    "requirements": {"status": "FAIL", "message": "ERROR: missing design.toml"},
                },
            }))

            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        assert "systemMessage" in output
                        assert "FAIL" in output["systemMessage"]
                        assert "design.toml" in output["systemMessage"]

    def test_main_handles_empty_stdin(self):
        """Handles empty/invalid stdin gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()  # Should not raise
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
