import re

with open("backend/app/risk/risk_engine.py", "r") as f:
    code = f.read()

code = code.replace(
    "if db and transaction.id:\n            self._persist_to_db(db, response, transaction)",
    "if db and transaction.id:\n            await self._persist_to_db(db, response, transaction)"
)

# Handle different possible formatted versions
code = re.sub(
    r"def _persist_to_db\(\s*self,\s*db:\s*(Session|AsyncSession),\s*response:\s*RiskResponse,\s*tx_input:\s*TransactionInput,?\s*\):",
    "async def _persist_to_db(self, db: AsyncSession, response: RiskResponse, tx_input: TransactionInput):",
    code
)

code = code.replace(
    "tx = db.query(Transaction).filter_by(id=response.transaction_id).first()",
    "res = await db.execute(select(Transaction).filter_by(id=response.transaction_id))\n            tx = res.scalar_one_or_none()"
)

with open("backend/app/risk/risk_engine.py", "w") as f:
    f.write(code)
