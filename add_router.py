import re

with open("backend/app/main.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    "from app.api.endpoints.risk import router as risk_router",
    "from app.api.endpoints.risk import router as risk_router\nfrom app.api.endpoints.behavior import router as behavior_router"
)

code = code.replace(
    "app.include_router(risk_router, prefix=api_prefix + \"/risk\", tags=[\"risk\"])",
    "app.include_router(risk_router, prefix=api_prefix + \"/risk\", tags=[\"risk\"])\n    app.include_router(behavior_router, prefix=api_prefix + \"/behavior\", tags=[\"behavior\"])"
)

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated main.py")
