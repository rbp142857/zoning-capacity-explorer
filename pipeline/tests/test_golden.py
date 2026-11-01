"""Each city's golden file must match what the Python engine computes today.

If this fails after you changed the engine, rules or scenarios, run
`make golden CITY=<city>` and commit the updated shared/fixtures/golden_<city>.json
(the browser parity test then checks the TypeScript engine against it).
"""

import json

import pytest

from zce.config import load_city
from zce.golden import GOLDEN_DIR, SCENARIOS, compute_expected

GOLDEN_FILES = sorted(GOLDEN_DIR.glob("golden_*.json"))


@pytest.mark.parametrize("path", GOLDEN_FILES, ids=[p.stem for p in GOLDEN_FILES])
def test_golden_file_is_current(path):
    golden = json.loads(path.read_text())
    assert set(golden["scenarios"]) == set(SCENARIOS), "scenario list changed: run `make golden`"
    expected = compute_expected(load_city(golden["city"]), golden["lots"])
    # JSON turns dict keys/ints the same way both times, so compare via JSON.
    assert json.loads(json.dumps(expected)) == golden["expected"], "engine output changed: run `make golden`"
