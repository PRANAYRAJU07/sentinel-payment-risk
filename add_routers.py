import re

with open("backend/app/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# Add imports
imports = """
from app.api.endpoints.dashboard import router as dashboard_router
from app.api.endpoints.transactions_api import router as transactions_router
from app.api.endpoints.investigations import router as investigations_router
from app.api.endpoints.analyst import router as analyst_router
from app.api.endpoints.webhooks import router as webhooks_router
from app.api.endpoints.simulator import router as simulator_router
from app.api.endpoints.audit import router as audit_router
from app.api.endpoints.graph_api import router as graph_router
from app.api.endpoints.models_api import router as models_router
"""

code = code.replace(
    "from app.api.endpoints.behavior import router as behavior_router",
    "from app.api.endpoints.behavior import router as behavior_router" + imports
)

# Add includes
includes = """
    app.include_router(dashboard_router, prefix=api_prefix + "/dashboard", tags=["Dashboard"])
    app.include_router(transactions_router, prefix=api_prefix + "/transactions", tags=["Transactions"])
    app.include_router(investigations_router, prefix=api_prefix + "/investigations", tags=["Investigations"])
    app.include_router(analyst_router, prefix=api_prefix + "/analyst-review", tags=["Analyst"])
    app.include_router(webhooks_router, prefix=api_prefix + "/webhooks", tags=["Webhooks"])
    app.include_router(simulator_router, prefix=api_prefix + "/simulator", tags=["Simulator"])
    app.include_router(audit_router, prefix=api_prefix + "/audit-log", tags=["Audit"])
    app.include_router(graph_router, prefix=api_prefix + "/graph", tags=["Graph"])
    app.include_router(models_router, prefix=api_prefix + "/models", tags=["Models"])
"""

code = code.replace(
    "app.include_router(behavior_router, prefix=api_prefix + \"/behavior\", tags=[\"behavior\"])",
    "app.include_router(behavior_router, prefix=api_prefix + \"/behavior\", tags=[\"behavior\"])\n" + includes
)

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated main.py")
