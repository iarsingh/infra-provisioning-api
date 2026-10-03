from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Provisioning API")


class StackRequest(BaseModel):
    name: str
    environment: str


@app.post("/stacks")
def create_stack(body: StackRequest):
    if body.environment in {"prod", "production"}:
        raise HTTPException(status_code=422, detail="prod is not rendered; change the GitOps repository")
    if body.environment not in {"dev", "staging"}:
        raise HTTPException(status_code=422, detail="environment must be dev or staging")
    main = (
        'module "service" {\n'
        '  source      = "../../modules/service"\n'
        f'  name        = "{body.name}"\n'
        f'  environment = "{body.environment}"\n'
        "}\n"
    )
    return {"applied": False, "files": {"main.tf": main}}
