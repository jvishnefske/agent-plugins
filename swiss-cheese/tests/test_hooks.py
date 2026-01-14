"""Unit tests for swiss-cheese gate_check hook."""
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
    LAYERS,
    get_project_dir,
    makefile_exists,
    has_target,
    run_gate,
    detect_current_layer,
    check_current_gate,
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


class TestMakefileExists:
    """Test makefile_exists function."""

    def test_makefile_exists(self):
        """Returns True when Makefile exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: test\ntest:\n\techo ok\n")
            assert makefile_exists(Path(tmpdir)) is True

    def test_makefile_missing(self):
        """Returns False when Makefile missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert makefile_exists(Path(tmpdir)) is False


class TestHasTarget:
    """Test has_target function."""

    def test_target_exists(self):
        """Returns True for existing target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: test\ntest:\n\t@echo ok\n")
            exists, err = has_target(Path(tmpdir), "test")
            assert exists is True
            assert err == ""

    def test_target_missing(self):
        """Returns False for missing target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: test\ntest:\n\t@echo ok\n")
            exists, _ = has_target(Path(tmpdir), "nonexistent")
            assert exists is False


class TestRunGate:
    """Test run_gate function."""

    def test_gate_passes(self):
        """Returns (True, output) when gate passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: test\ntest:\n\t@echo 'Gate passed'\n")
            passed, output = run_gate(Path(tmpdir), "test")
            assert passed is True
            assert "Gate passed" in output

    def test_gate_fails(self):
        """Returns (False, output) when gate fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: test\ntest:\n\t@echo 'Error' && exit 1\n")
            passed, output = run_gate(Path(tmpdir), "test")
            assert passed is False
            assert "Error" in output

    def test_gate_timeout(self):
        """Returns (False, message) on timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: slow\nslow:\n\tsleep 10\n")
            passed, output = run_gate(Path(tmpdir), "slow", timeout=1)
            assert passed is False
            assert "timed out" in output

    def test_output_truncated(self):
        """Output is truncated to last 500 chars."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            # Generate long output
            makefile.write_text(
                ".PHONY: verbose\nverbose:\n\t@python3 -c \"print('x' * 1000)\"\n"
            )
            passed, output = run_gate(Path(tmpdir), "verbose")
            assert passed is True
            assert len(output) <= 500


class TestDetectCurrentLayer:
    """Test detect_current_layer function."""

    def test_no_makefile_returns_1(self):
        """Returns layer 1 when no Makefile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layer = detect_current_layer(Path(tmpdir))
            assert layer == 1

    def test_all_pass_returns_4(self):
        """Returns layer 4 when all gates pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            targets = "\n".join(
                f".PHONY: {target}\n{target}:\n\t@echo ok"
                for _, target in LAYERS.values()
            )
            makefile.write_text(targets)
            layer = detect_current_layer(Path(tmpdir))
            assert layer == 4

    def test_first_failure_detected(self):
        """Returns first failing layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            # Layer 1 passes, Layer 2 fails
            makefile.write_text(
                ".PHONY: validate-requirements validate-tdd\n"
                "validate-requirements:\n\t@echo ok\n"
                "validate-tdd:\n\t@exit 1\n"
            )
            layer = detect_current_layer(Path(tmpdir))
            assert layer == 2


class TestCheckCurrentGate:
    """Test check_current_gate function."""

    def test_unknown_layer(self):
        """Returns NOT_RUN for unknown layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_current_gate(Path(tmpdir), 99)
            assert result.status == GateStatus.NOT_RUN
            assert result.name == "unknown"

    def test_no_makefile(self):
        """Returns NOT_RUN when no Makefile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_current_gate(Path(tmpdir), 1)
            assert result.status == GateStatus.NOT_RUN
            assert result.message == "No Makefile"

    def test_no_target(self):
        """Returns NOT_RUN when target missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: other\nother:\n\t@echo ok\n")
            result = check_current_gate(Path(tmpdir), 1)
            assert result.status == GateStatus.NOT_RUN
            assert "No target" in result.message

    def test_gate_passes(self):
        """Returns PASS when gate succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(
                ".PHONY: validate-requirements\n"
                "validate-requirements:\n\t@echo ok\n"
            )
            result = check_current_gate(Path(tmpdir), 1)
            assert result.status == GateStatus.PASS
            assert result.name == "requirements"
            assert result.message is None

    def test_gate_fails(self):
        """Returns FAIL with output when gate fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(
                ".PHONY: validate-requirements\n"
                "validate-requirements:\n\t@echo 'ERROR: missing file' && exit 1\n"
            )
            result = check_current_gate(Path(tmpdir), 1)
            assert result.status == GateStatus.FAIL
            assert result.name == "requirements"
            assert "missing file" in result.message


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


class TestMain:
    """Test main function (hook entry point)."""

    def test_main_no_makefile_continues(self):
        """Continues silently when no Makefile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        assert "systemMessage" not in output

    def test_main_no_validate_targets_continues(self):
        """Continues silently when no validate-* targets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(".PHONY: test\ntest:\n\t@echo ok\n")
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        assert "systemMessage" not in output

    def test_main_gate_pass_continues_silently(self):
        """Continues silently when gate passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(
                ".PHONY: validate-requirements\n"
                "validate-requirements:\n\t@echo ok\n"
            )
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        # No system message on pass
                        assert "systemMessage" not in output

    def test_main_gate_fail_shows_message(self):
        """Shows system message when gate fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile = Path(tmpdir) / "Makefile"
            makefile.write_text(
                ".PHONY: validate-requirements\n"
                "validate-requirements:\n\t@echo 'ERROR: missing design.md' && exit 1\n"
            )
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("{}")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
                        assert "systemMessage" in output
                        assert "FAIL" in output["systemMessage"]
                        assert "missing design.md" in output["systemMessage"]

    def test_main_handles_empty_stdin(self):
        """Handles empty/invalid stdin gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": tmpdir}):
                with patch("sys.stdin", StringIO("")):
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        main()  # Should not raise
                        output = json.loads(mock_stdout.getvalue())
                        assert output["continue"] is True
