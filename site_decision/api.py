from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
import yaml
import os

from site_decision.engine import evaluate

app = FastAPI(title="Site Capacity Upgrade Decision Service")

# Load configuration (in a real scenario, could be managed dynamically or via env)
CONFIG_PATH = os.environ.get("SITE_CONFIG_PATH", "site_decision/config/default_operator.yaml")
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

class SiteInput(BaseModel):
    model_config = ConfigDict(extra="allow")  # Forward-compatible: unknown fields pass through
    site_id: str
    site_type: str
    current_load_pct: float | None = None
    spectrum_available: bool | None = None
    backhaul_capacity_mbps: float | None = None
    backhaul_required_mbps: float | None = None
    power_headroom_kw: float | None = None
    power_required_kw: float | None = None

@app.post("/evaluate")
def evaluate_site(site: SiteInput):
    if site.site_type not in CONFIG.get("site_types", {}):
        raise HTTPException(status_code=400, detail=f"Unknown site_type: {site.site_type}")

    decision = evaluate(site.model_dump(), CONFIG)
    
    # Simple serialization for response
    def _serialize(obj):
        if hasattr(obj, 'value'):
            return obj.value
        if isinstance(obj, list):
            return [_serialize(i) for i in obj]
        if hasattr(obj, '__dict__'):
            return {k: _serialize(v) for k, v in obj.__dict__.items()}
        return obj

    return _serialize(decision)

@app.get("/health")
def health():
    return {"status": "ok"}
