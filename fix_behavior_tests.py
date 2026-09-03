import re
import os

# 1. Fix backend/tests/risk/test_behavioral.py (async)
with open("backend/tests/risk/test_behavioral.py", "r") as f:
    code = f.read()

code = code.replace("import pytest", "import pytest\nimport asyncio")
code = code.replace("def test_missing_baseline():", "@pytest.mark.asyncio\nasync def test_missing_baseline():")
code = code.replace("def test_amount_anomaly():", "@pytest.mark.asyncio\nasync def test_amount_anomaly():")
code = code.replace("def test_time_anomaly():", "@pytest.mark.asyncio\nasync def test_time_anomaly():")

code = code.replace("res = engine.evaluate(tx)", "res = await engine.evaluate(tx)")

with open("backend/tests/risk/test_behavioral.py", "w") as f:
    f.write(code)

# 2. Fix test_insufficient_history. Let's check what it actually returned.
with open("backend/tests/behavior/test_behavioral_api.py", "r") as f:
    code = f.read()

code = code.replace("assert res.json()[\"profile_status\"] == \"INSUFFICIENT_HISTORY\"", "data = res.json()\n    print(data)\n    assert data.get(\"profile_status\") == \"INSUFFICIENT_HISTORY\"")

with open("backend/tests/behavior/test_behavioral_api.py", "w") as f:
    f.write(code)

print("Tests updated")
