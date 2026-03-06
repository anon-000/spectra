from spectra.tasks.normalizer import compute_fingerprint, deduplicate
from spectra.tasks.tools.base import RawFinding


def test_compute_fingerprint_deterministic():
    f = RawFinding(tool="semgrep", rule_id="r1", file_path="a.py", snippet="x = 1")
    assert compute_fingerprint(f) == compute_fingerprint(f)


def test_compute_fingerprint_different_for_different_input():
    f1 = RawFinding(tool="semgrep", rule_id="r1", file_path="a.py")
    f2 = RawFinding(tool="semgrep", rule_id="r2", file_path="a.py")
    assert compute_fingerprint(f1) != compute_fingerprint(f2)


def test_deduplicate():
    f1 = RawFinding(tool="semgrep", rule_id="r1", file_path="a.py", snippet="x")
    f2 = RawFinding(tool="semgrep", rule_id="r1", file_path="a.py", snippet="x")  # dup
    f3 = RawFinding(tool="semgrep", rule_id="r2", file_path="b.py")

    result = deduplicate([f1, f2, f3])
    assert len(result) == 2
