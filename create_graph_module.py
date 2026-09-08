import os

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

write_file("backend/app/graph/__init__.py", "")

# backend/app/graph/graph_builder.py
write_file("backend/app/graph/graph_builder.py", """
import networkx as nx
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transactions import Transaction

class GraphBuilder:
    def __init__(self):
        self.graph = nx.Graph()

    async def build_from_transactions(self, db: AsyncSession, limit: int = 5000):
        \"\"\"
        Builds a NetworkX graph from recent transactions to map entity relationships.
        Nodes: Customer, Merchant, Device, IP, Transaction
        Edges: customer_transaction, device_transaction, ip_transaction, merchant_transaction
        \"\"\"
        stmt = select(Transaction).order_by(Transaction.time.desc()).limit(limit)
        result = await db.execute(stmt)
        transactions = result.scalars().all()
        
        for t in transactions:
            tx_node = f"TX_{t.id}"
            self.graph.add_node(tx_node, type="TRANSACTION", amount=t.amount, time=t.time, status=t.status)
            
            if t.customer_id:
                cust_node = f"CUST_{t.customer_id}"
                self.graph.add_node(cust_node, type="CUSTOMER")
                self.graph.add_edge(cust_node, tx_node, relation="CREATED")
                
            if t.merchant_id:
                merch_node = f"MERCH_{t.merchant_id}"
                self.graph.add_node(merch_node, type="MERCHANT")
                self.graph.add_edge(tx_node, merch_node, relation="PAID_TO")
                
            if t.device_id:
                dev_node = f"DEV_{t.device_id}"
                self.graph.add_node(dev_node, type="DEVICE")
                self.graph.add_edge(cust_node if t.customer_id else tx_node, dev_node, relation="USED_DEVICE")
                
            if t.ip_address:
                ip_node = f"IP_{t.ip_address}"
                self.graph.add_node(ip_node, type="IP")
                self.graph.add_edge(cust_node if t.customer_id else tx_node, ip_node, relation="USED_IP")
                
        return self.graph

    def update_with_transaction(self, tx_data: dict):
        \"\"\"
        Incrementally adds a transaction to the in-memory graph.
        \"\"\"
        tx_node = f"TX_{tx_data.get('id')}"
        self.graph.add_node(tx_node, type="TRANSACTION", amount=tx_data.get('amount'), time=tx_data.get('time'))
        
        cust_id = tx_data.get("customer_id")
        merch_id = tx_data.get("merchant_id")
        dev_id = tx_data.get("device_id")
        ip = tx_data.get("ip_address")
        
        if cust_id:
            cust_node = f"CUST_{cust_id}"
            self.graph.add_node(cust_node, type="CUSTOMER")
            self.graph.add_edge(cust_node, tx_node, relation="CREATED")
            
            if dev_id:
                dev_node = f"DEV_{dev_id}"
                self.graph.add_node(dev_node, type="DEVICE")
                self.graph.add_edge(cust_node, dev_node, relation="USED_DEVICE")
                
            if ip:
                ip_node = f"IP_{ip}"
                self.graph.add_node(ip_node, type="IP")
                self.graph.add_edge(cust_node, ip_node, relation="USED_IP")
                
        if merch_id:
            merch_node = f"MERCH_{merch_id}"
            self.graph.add_node(merch_node, type="MERCHANT")
            self.graph.add_edge(tx_node, merch_node, relation="PAID_TO")

    def get_graph(self):
        return self.graph
""")

# backend/app/graph/graph_features.py
write_file("backend/app/graph/graph_features.py", """
import networkx as nx
from typing import Dict, Any

class GraphFeatureExtractor:
    @staticmethod
    def extract_features(graph: nx.Graph, entity_node: str) -> Dict[str, Any]:
        \"\"\"
        Extracts structural features for a given entity node.
        \"\"\"
        if entity_node not in graph:
            return {
                "degree": 0,
                "connected_devices": 0,
                "connected_ips": 0,
                "connected_accounts": 0,
                "is_isolated": True
            }
            
        # Get neighbors
        neighbors = list(graph.neighbors(entity_node))
        degree = len(neighbors)
        
        # Traverse up to 2 hops to find connected components
        devices = set()
        ips = set()
        accounts = set()
        
        for n in neighbors:
            ntype = graph.nodes[n].get("type")
            if ntype == "DEVICE":
                devices.add(n)
                # Find accounts sharing this device
                for n2 in graph.neighbors(n):
                    if graph.nodes[n2].get("type") == "CUSTOMER" and n2 != entity_node:
                        accounts.add(n2)
            elif ntype == "IP":
                ips.add(n)
                # Find accounts sharing this IP
                for n2 in graph.neighbors(n):
                    if graph.nodes[n2].get("type") == "CUSTOMER" and n2 != entity_node:
                        accounts.add(n2)
                        
        return {
            "degree": degree,
            "connected_devices": len(devices),
            "connected_ips": len(ips),
            "connected_accounts": len(accounts),
            "is_isolated": len(accounts) == 0
        }
""")

# backend/app/graph/cluster_detector.py
write_file("backend/app/graph/cluster_detector.py", """
import networkx as nx
from typing import List, Dict, Any

class ClusterDetector:
    @staticmethod
    def detect_clusters(graph: nx.Graph) -> List[Dict[str, Any]]:
        \"\"\"
        Detects densely connected suspicious clusters based on shared devices/IPs.
        \"\"\"
        clusters = []
        components = list(nx.connected_components(graph))
        
        for idx, comp in enumerate(components):
            if len(comp) < 3: # Ignore trivial components
                continue
                
            customers = [n for n in comp if graph.nodes[n].get("type") == "CUSTOMER"]
            devices = [n for n in comp if graph.nodes[n].get("type") == "DEVICE"]
            ips = [n for n in comp if graph.nodes[n].get("type") == "IP"]
            
            # If multiple customers share a single device or IP, that's a cluster
            if len(customers) > 1 and (len(devices) > 0 or len(ips) > 0):
                cluster_risk = min(len(customers) * 15 + len(devices) * 10, 100)
                clusters.append({
                    "cluster_id": f"CL-{idx}",
                    "size": len(comp),
                    "customers": len(customers),
                    "devices": len(devices),
                    "ips": len(ips),
                    "risk_score": cluster_risk,
                    "nodes": list(comp)
                })
                
        return clusters
""")

# backend/app/graph/graph_service.py
write_file("backend/app/graph/graph_service.py", """
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
        \"\"\"
        Calculates real-time graph risk by checking for shared device/IP abuse.
        \"\"\"
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
""")

print("Graph module created.")
