"""The golden file must match what the Python engine computes today.

If this fails after you changed the engine, rules or scenarios, run
`make golden` and commit the updated shared/fixtures/golden.json (the
browser parity test then checks the TypeScript engine against it).
"""

import json

import pytest

from zce.config import load_city
from zce.golden import GOLDEN_PATH, SCENARIOS, compute_expected


@pytest.mark.skipif(not GOLDEN_PATH.exists(), reason="golden file not generated yet")
def test_golden_file_is_current():
    golden = json.loads(GOLDEN_PATH.read_text())
    assert set(golden["scenarios"]) == set(SCENARIOS), "scenario list changed: run `make golden`"
    expected = compute_expected(load_city(golden["city"]), golden["lots"])
    # JSON turns dict keys/ints the same way both times, so compare via JSON.
    assert json.loads(json.dumps(expected)) == golden["expected"], "engine output changed: run `make golden`"
