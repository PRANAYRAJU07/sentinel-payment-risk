"""
Sentinel Risk Engine — Orchestrator
Aggregates all risk signals, makes final decision, generates trace, and persists to DB.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import get_settings
from app.models.transactions import AuditLog, RiskScore, Transaction
from app.risk.behavioral import BehavioralAnalyzer
from app.risk.graph_signal import GraphRiskSignal
from app.risk.risk_factors import RuleEngine
from app.risk.risk_policy import DecisionEngine
from app.risk.risk_response import RiskResponse, SignalResponse, TransactionInput

try:
    from ml.src.inference.model_predictor import RiskPredictor
except ImportError:
    RiskPredictor = None

logger = logging.getLogger(__name__)


class RiskEngineOrchestrator:
    def __init__(self):
        self.settings = get_settings()
        self.rule_engine = RuleEngine()
        self.behavioral_engine = BehavioralAnalyzer()
        self.graph_engine = GraphRiskSignal()
        self.decision_engine = DecisionEngine()

        self.ml_predictor = None
        if RiskPredictor is not None:
            try:
                self.ml_predictor = RiskPredictor()
            except Exception as e:
                logger.warning(f"Failed to load ML Predictor: {e}")

    async def evaluate(
        self, transaction: TransactionInput, db: AsyncSession = None
    ) -> RiskResponse:
        logger.info(f"Evaluating transaction: {transaction.id}")

        # 1. ML Signal
        ml_res = SignalResponse(available=False)
        model_version = "none"
        if self.ml_predictor:
            try:
                tx_dict = transaction.model_dump()
                tx_dict["Time"] = transaction.time
                tx_dict["Amount"] = transaction.amount

                # For V features
                for k, v in transaction.v_features.items():
                    tx_dict[k] = v

                score_out = self.ml_predictor.score_transaction(tx_dict)
                prob = score_out.get("probability", 0.0)
                ml_score = min(prob * 100, 100.0)  # Convert to 0-100 prototype score

                reasons = []
                if ml_score >= self.settings.risk_high_threshold:
                    reasons.append(
                        {
                            "reason_code": "ML_HIGH_RISK",
                            "severity": "HIGH",
                            "message": "ML model assigned a high transaction risk score",
                        }
                    )

                ml_res = SignalResponse(available=True, score=ml_score, reasons=reasons)
                model_version = score_out.get("model_used", "unknown")
            except Exception as e:
                logger.error(f"ML Predictor failed: {e}")

        # 2. Behavioral Signal
        beh_res = await self.behavioral_engine.evaluate(transaction, db)

        # 3. Rule Signal
        rule_res = self.rule_engine.evaluate(transaction)

        # 4. Graph Signal
        graph_res = self.graph_engine.evaluate(transaction)

        # 5. Aggregation
        final_score = self._aggregate_scores(ml_res, beh_res, rule_res, graph_res)

        # 6. Decision Policy & Overrides
        risk_level, decision, override_reason = self.decision_engine.evaluate(
            final_score, transaction
        )

        # Collect all reasons
        all_reasons = []
        if override_reason:
            all_reasons.append(override_reason)
        all_reasons.extend(ml_res.reasons)
        all_reasons.extend(beh_res.reasons)
        all_reasons.extend(rule_res.reasons)
        all_reasons.extend(graph_res.reasons)

        response = RiskResponse(
            transaction_id=transaction.id or "dummy",
            ml_risk_score=ml_res.score,
            behavioral_risk_score=beh_res.score,
            rule_risk_score=rule_res.score,
            graph_risk_score=graph_res.score,
            final_risk_score=int(final_score),
            risk_level=risk_level,
            decision=decision,
            reasons=all_reasons,
            model_version=model_version,
            policy_version="policy-v1",
            signal_availability={
                "ml": ml_res.available,
                "behavioral": beh_res.available,
                "rule": rule_res.available,
                "graph": graph_res.available,
            },
        )

        # 7. Persist to DB if provided
        if db and transaction.id:
            await self._persist_to_db(db, response, transaction)

        return response

    def _aggregate_scores(
        self,
        ml: SignalResponse,
        beh: SignalResponse,
        rule: SignalResponse,
        graph: SignalResponse,
    ) -> float:
        """Aggregates scores, renormalizing weights if a signal is unavailable."""
        weights = {
            "ml": self.settings.risk_ml_weight if ml.available else 0.0,
            "beh": self.settings.risk_behavior_weight if beh.available else 0.0,
            "rule": self.settings.risk_rule_weight if rule.available else 0.0,
            "graph": self.settings.risk_graph_weight if graph.available else 0.0,
        }

        total_weight = sum(weights.values())
        if total_weight == 0.0:
            return 0.0

        # Renormalize
        norm_weights = {k: v / total_weight for k, v in weights.items()}

        final = (
            (ml.score * norm_weights["ml"])
            + (beh.score * norm_weights["beh"])
            + (rule.score * norm_weights["rule"])
            + (graph.score * norm_weights["graph"])
        )

        return min(final, 100.0)

    async def _persist_to_db(self, db: AsyncSession, response: RiskResponse, tx_input: TransactionInput):
        """Saves RiskScore and AuditLog to the database, ensuring idempotency."""
        try:
            # Ensure transaction exists before we can link risk score to it
            res = await db.execute(select(Transaction).filter_by(id=response.transaction_id))
            tx = res.scalar_one_or_none()
            if not tx:
                logger.warning(
                    f"Transaction {response.transaction_id} not found in DB. Skipping DB persist."
                )
                return

            # Upsert Risk Score
            stmt = insert(RiskScore).values(
                id=str(uuid.uuid4()),
                transaction_id=response.transaction_id,
                risk_score=response.final_risk_score,
                decision=response.decision,
                ml_score=response.ml_risk_score,
                behavioral_score=response.behavioral_risk_score,
                graph_score=response.graph_risk_score,
                model_version=response.model_version,
                features_snapshot=tx_input.model_dump(),
                risk_reasons=response.reasons,
                scored_at=datetime.now(timezone.utc),
            )

            # Idempotency: if risk score for this tx exists, do nothing (or update)
            # For now, we update it.
            stmt = stmt.on_conflict_do_update(
                index_elements=["transaction_id"],
                set_={
                    "risk_score": stmt.excluded.risk_score,
                    "decision": stmt.excluded.decision,
                    "ml_score": stmt.excluded.ml_score,
                    "behavioral_score": stmt.excluded.behavioral_score,
                    "graph_score": stmt.excluded.graph_score,
                    "model_version": stmt.excluded.model_version,
                    "features_snapshot": stmt.excluded.features_snapshot,
                    "risk_reasons": stmt.excluded.risk_reasons,
                    "scored_at": stmt.excluded.scored_at,
                },
            )
            await db.execute(stmt)

            # Append Audit Log
            audit = AuditLog(
                transaction_id=response.transaction_id,
                event_id=f"risk_eval_{response.transaction_id}_{uuid.uuid4().hex[:8]}",
                action="RISK_DECISION",
                actor="SYSTEM",
                details={
                    "decision": response.decision,
                    "risk_score": response.final_risk_score,
                    "model_version": response.model_version,
                    "policy_version": response.policy_version,
                },
            )
            db.add(audit)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to persist risk score to DB: {e}")
