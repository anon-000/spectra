import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from spectra.schemas.policy import PolicyEvalResult


def test_policy_eval_result_passed():
    result = PolicyEvalResult(passed=True, violations=[])
    assert result.passed
    assert result.violations == []


def test_policy_eval_result_failed():
    result = PolicyEvalResult(
        passed=False,
        violations=["Policy 'strict': critical finding 'SQL Injection'"],
    )
    assert not result.passed
    assert len(result.violations) == 1
