import re
import os

# 1. Fix demo_risk_engine.py to use async
with open("scripts/demo_risk_engine.py", "r") as f:
    code = f.read()
code = code.replace("import sys\nimport time\nimport uuid", "import sys\nimport time\nimport uuid\nimport asyncio")
code = code.replace("def main():", "async def main():")
code = code.replace("res_a = engine.evaluate(tx_a)", "res_a = await engine.evaluate(tx_a)")
code = code.replace("res_b = engine.evaluate(tx_b)", "res_b = await engine.evaluate(tx_b)")
code = code.replace("res_c = engine.evaluate(tx_c)", "res_c = await engine.evaluate(tx_c)")
code = code.replace("engine.evaluate(tx_bench)", "await engine.evaluate(tx_bench)")
code = code.replace("if __name__ == \"__main__\":\n    main()", "if __name__ == \"__main__\":\n    asyncio.run(main())")
with open("scripts/demo_risk_engine.py", "w") as f:
    f.write(code)

# 2. Fix test_risk_engine.py
with open("backend/tests/risk/test_risk_engine.py", "r") as f:
    code = f.read()
code = code.replace("import uuid", "import uuid\nimport pytest\nimport asyncio")
code = code.replace("def test_engine_evaluation_mocked():", "@pytest.mark.asyncio\nasync def test_engine_evaluation_mocked():")
code = code.replace("res = engine.evaluate(tx, db=None)", "res = await engine.evaluate(tx, db=None)")
with open("backend/tests/risk/test_risk_engine.py", "w") as f:
    f.write(code)

# 3. Fix backend/app/api/endpoints/risk.py to use async
with open("backend/app/api/endpoints/risk.py", "r") as f:
    code = f.read()

code = code.replace("from sqlalchemy.orm import Session", "from sqlalchemy.ext.asyncio import AsyncSession\nfrom sqlalchemy.future import select")
code = code.replace("db: Session", "db: AsyncSession")

code = code.replace("def evaluate_risk", "async def evaluate_risk")
code = code.replace("response = risk_engine.evaluate(transaction, db)", "response = await risk_engine.evaluate(transaction, db)")

code = code.replace("def get_risk_evaluation", "async def get_risk_evaluation")
code = code.replace("score = db.query(RiskScore).filter(RiskScore.transaction_id == transaction_id).first()", 
                    "res = await db.execute(select(RiskScore).filter(RiskScore.transaction_id == transaction_id))\n    score = res.scalar_one_or_none()")

code = code.replace("def get_risk_trace", "async def get_risk_trace")
code = code.replace("score = db.query(RiskScore).filter(RiskScore.transaction_id == transaction_id).first()", 
                    "res = await db.execute(select(RiskScore).filter(RiskScore.transaction_id == transaction_id))\n    score = res.scalar_one_or_none()")

with open("backend/app/api/endpoints/risk.py", "w") as f:
    f.write(code)

print("Fixes applied.")
