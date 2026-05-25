"""Shared test fixtures.

Resets the shared rate limiter between tests so that one test's calls do not
count against another's per-correlation-id budget.
"""

from __future__ import annotations

import pytest

from shared.ratelimit import shared_rate_limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    shared_rate_limiter.reset()
    yield
    shared_rate_limiter.reset()
