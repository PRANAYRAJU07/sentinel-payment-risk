with open("backend/tests/risk/test_behavioral.py", "r") as f:
    code = f.read()
if "import pytest" not in code:
    code = "import pytest\nimport asyncio\n" + code
with open("backend/tests/risk/test_behavioral.py", "w") as f:
    f.write(code)
