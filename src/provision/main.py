from provision.ops import router as ops_router
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from provision.render import REGIONS, SIZE_CAP, SIZES, RenderError, render

app = FastAPI(title="Provisioning API")
app.include_router(ops_router, prefix="/v1")


class StackRequest(BaseModel):
    name: str
    environment: str
    region: str = "us-central1"
    size: str = "small"
    team: str = ""
    cost_center: str = ""


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/options")
def options():
    return {"regions": list(REGIONS), "sizes": SIZES, "size_cap": SIZE_CAP}


@app.post("/stacks")
def create_stack(body: StackRequest):
    try:
        return render(body.model_dump())
    except RenderError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
