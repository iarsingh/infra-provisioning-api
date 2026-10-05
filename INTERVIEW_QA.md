# infra-provisioning-api — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does infra-provisioning-api address, and what can you demonstrate?

`POST /stacks` validates a request and returns three Terraform files: `main.tf` calling `terraform/modules/service`, `variables.tf`, and `terraform.tfvars`. It also returns a monthly estimate for the chosen size. `applied` is false. Nothing here runs `terraform apply`, and GCP credentials are not read. The next step is a pull request.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/provision/main.py`](src/provision/main.py): Implementation or supporting configuration.
- [`src/provision/ops.py`](src/provision/ops.py): Implementation or supporting configuration.
- [`src/provision/render.py`](src/provision/render.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`terraform/modules/service/main.tf`](terraform/modules/service/main.tf): Terraform resource/module declarations.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `render` and explain the decision it makes?

The main walkthrough here is `render(request)` in [`src/provision/render.py`](src/provision/render.py#L39).

```python
def render(request):
    validate(request)
    size = SIZES[request["size"]]
    main = (
        'module "service" {\n'
        '  source       = "../../modules/service"\n'
        "  name         = var.name\n"
        "  environment  = var.environment\n"
        "  region       = var.region\n"
        "  machine_type = var.machine_type\n"
        "  labels       = var.labels\n"
        "}\n"
    )
    variables = (
        'variable "name" { type = string }\n'
        'variable "environment" { type = string }\n'
        'variable "region" { type = string }\n'
        'variable "machine_type" { type = string }\n'
        'variable "labels" { type = map(string) }\n'
    )
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `validate`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `validate` have?

`validate(request)` is defined in [`src/provision/render.py`](src/provision/render.py#L20).

It uses `', '.join`, `LABEL.fullmatch`, `NAME.fullmatch`, `ORDER.index`, `RenderError`, `request.get`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=422, detail=str(exc))` in [`src/provision/main.py`](src/provision/main.py#L35).
- `HTTPException(status_code=404, detail='workspace not found')` in [`src/provision/ops.py`](src/provision/ops.py#L77).
- `HTTPException(status_code=404, detail='job not found')` in [`src/provision/ops.py`](src/provision/ops.py#L100).
- `HTTPException(status_code=404, detail='job not found')` in [`src/provision/ops.py`](src/provision/ops.py#L109).
- `HTTPException(status_code=403, detail='production apply is disabled in this lab')` in [`src/provision/ops.py`](src/provision/ops.py#L113).
- `RenderError('prod is not rendered; change the GitOps repository')` in [`src/provision/render.py`](src/provision/render.py#L22).
- `RenderError('environment must be dev or staging')` in [`src/provision/render.py`](src/provision/render.py#L24).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_ops.py`](tests/test_ops.py#L8) contains `test_readyz`:

```python
def test_readyz():
    r = client.get("/v1/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/provision/main.py`](src/provision/main.py#L21).
- `GET /options` → `options` in [`src/provision/main.py`](src/provision/main.py#L26).
- `POST /stacks` → `create_stack` in [`src/provision/main.py`](src/provision/main.py#L31).
- `GET /readyz` → `readyz` in [`src/provision/ops.py`](src/provision/ops.py#L44).
- `POST /workspaces` → `create_workspace` in [`src/provision/ops.py`](src/provision/ops.py#L49).
- `GET /workspaces` → `list_workspaces` in [`src/provision/ops.py`](src/provision/ops.py#L66).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/provision/ops.py`](src/provision/ops.py#L73).
- `GET /jobs/{job_id}` → `get_job` in [`src/provision/ops.py`](src/provision/ops.py#L96).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/provision/ops.py`](src/provision/ops.py); `SIZES`, `SIZE_CAP` in [`src/provision/render.py`](src/provision/render.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `render`?

In [`src/provision/render.py`](src/provision/render.py#L39), `render(request)` receives the inputs. The function computes these intermediate values:

- `size = SIZES[request['size']]`
- `main = 'module "service" {\n  source       = "../../modules/service"\n  name         = var.name\n  environment  = var.environment\n  region       = var.region\n  machine_type = var.machine_type\n  labels       = var.labels\n}\n'`
- `variables = 'variable "name" { type = string }\nvariable "environment" { type = string }\nvariable "region" { type = string }\nvariable "machine_type" { type = string }\nvariable "labels" { type = map(string) }\n'`
- `tfvars = f'''name         = "{request['name']}"\nenvironment  = "{request['environment']}"\nregion       = "{request['region']}"\nmachine_type = "{size['machine_type']}"\nlabels = {{\n  team        = "{request['team']}"\n  cost_center = "{request['cost_center']}"\n  environment = "{request['environment']}"\n  managed_by  = "provisioning-api"\n}}\n'''`

Its result is defined by:

- `{'applied': False, 'estimate': {'machine_type': size['machine_type'], 'monthly_usd': size['monthly_usd']}, 'files': {'main.tf': main, 'variables.tf': variables, 'terraform.tfvars': tfvars}, 'next_step': 'Open a pull request with these files. A reviewed pipeline runs terraform plan and apply.'}`

## 13. What does the operations plane add, and where is its limit?

[`src/provision/ops.py`](src/provision/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
