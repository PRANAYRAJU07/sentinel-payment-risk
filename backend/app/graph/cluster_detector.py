import networkx as nx
from typing import List, Dict, Any

class ClusterDetector:
    @staticmethod
    def detect_clusters(graph: nx.Graph) -> List[Dict[str, Any]]:
        """
        Detects densely connected suspicious clusters based on shared devices/IPs.
        """
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
