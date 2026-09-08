import networkx as nx
from typing import Dict, Any

class GraphFeatureExtractor:
    @staticmethod
    def extract_features(graph: nx.Graph, entity_node: str) -> Dict[str, Any]:
        """
        Extracts structural features for a given entity node.
        """
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
