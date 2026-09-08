import asyncio
from typing import Dict, Any, List
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession
from app.graph.graph_builder import GraphBuilder
from app.graph.graph_features import GraphFeatureExtractor
from app.graph.cluster_detector import ClusterDetector
from app.risk.risk_response import TransactionInput, SignalResponse

class GraphService:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphService, cls).__new__(cls)
            cls._instance.builder = GraphBuilder()
            cls._instance.initialized = False
        return cls._instance

    async def initialize(self, db: AsyncSession):
        async with self._lock:
            if not self.initialized:
                await self.builder.build_from_transactions(db, limit=5000)
                self.initialized = True
                
    async def get_graph_signal(self, tx: TransactionInput, db: AsyncSession = None) -> SignalResponse:
        """
        Calculates real-time graph risk by checking for shared device/IP abuse.
        """
        if db and not self.initialized:
            await self.initialize(db)
            
        # Temporarily add transaction to graph
        tx_data = {
            "id": tx.id,
            "amount": tx.amount,
            "time": tx.time,
            "customer_id": tx.customer_id,
            "merchant_id": tx.merchant_id,
            "device_id": tx.context.get("device_id"),
            "ip_address": tx.context.get("ip_address")
        }
        
        self.builder.update_with_transaction(tx_data)
        
        if not tx.customer_id:
            return SignalResponse(available=False)
            
        cust_node = f"CUST_{tx.customer_id}"
        graph = self.builder.get_graph()
        
        features = GraphFeatureExtractor.extract_features(graph, cust_node)
        
        reasons = []
        score = 0.0
        cluster_id = None
        
        # Check connected accounts (Device/IP sharing)
        conn_accounts = features.get("connected_accounts", 0)
        if conn_accounts > 0:
            score += min(conn_accounts * 25.0, 100.0)
            reasons.append({
                "reason_code": "GRAPH_SHARED_ENTITIES",
                "severity": "HIGH" if conn_accounts > 2 else "MEDIUM",
                "message": f"Account shares device or IP with {conn_accounts} other accounts."
            })
            
            # Simple clustering identifier for response
            cluster_id = f"CL-AUTO-{tx.customer_id[-4:]}"
            
        if score == 0:
            return SignalResponse(available=True, score=0.0)
            
        return SignalResponse(
            available=True,
            score=min(score, 100.0),
            reasons=reasons,
            metadata={"cluster_id": cluster_id, "connected_accounts": conn_accounts} if cluster_id else {}
        )
