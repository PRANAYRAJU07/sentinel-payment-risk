from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.graph.graph_service import GraphService

router = APIRouter()
graph_service = GraphService()

@router.get("/entity/{entity_id}")
async def get_entity_graph(entity_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the ego-graph (neighborhood) of a specific entity (e.g. CUST_123, DEV_abc)
    for frontend visualization.
    """
    if not graph_service.initialized:
        await graph_service.initialize(db)
        
    g = graph_service.builder.get_graph()
    
    # Check if entity exists
    if entity_id not in g:
        raise HTTPException(status_code=404, detail="Entity not found in graph")
        
    # Get 1-hop and 2-hop neighbors
    neighbors = list(g.neighbors(entity_id))
    nodes = {entity_id}
    nodes.update(neighbors)
    
    for n in neighbors:
        nodes.update(g.neighbors(n))
        
    # Build frontend-friendly representation
    subgraph = g.subgraph(nodes)
    
    frontend_nodes = []
    frontend_edges = []
    
    for n, data in subgraph.nodes(data=True):
        frontend_nodes.append({
            "id": n,
            "data": {"label": n, "type": data.get("type", "UNKNOWN")}
        })
        
    for u, v, data in subgraph.edges(data=True):
        frontend_edges.append({
            "id": f"{u}-{v}",
            "source": u,
            "target": v,
            "label": data.get("relation", "")
        })
        
    return {
        "nodes": frontend_nodes,
        "edges": frontend_edges
    }
