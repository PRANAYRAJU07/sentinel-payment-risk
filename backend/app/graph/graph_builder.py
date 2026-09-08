import networkx as nx
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transactions import Transaction

class GraphBuilder:
    def __init__(self):
        self.graph = nx.Graph()

    async def build_from_transactions(self, db: AsyncSession, limit: int = 5000):
        """
        Builds a NetworkX graph from recent transactions to map entity relationships.
        Nodes: Customer, Merchant, Device, IP, Transaction
        Edges: customer_transaction, device_transaction, ip_transaction, merchant_transaction
        """
        stmt = select(Transaction).order_by(Transaction.transaction_at.desc()).limit(limit)
        result = await db.execute(stmt)
        transactions = result.scalars().all()
        
        for t in transactions:
            tx_node = f"TX_{t.id}"
            self.graph.add_node(tx_node, type="TRANSACTION", amount=t.amount, time=t.transaction_at.timestamp(), status=t.status)
            
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
        """
        Incrementally adds a transaction to the in-memory graph.
        """
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
