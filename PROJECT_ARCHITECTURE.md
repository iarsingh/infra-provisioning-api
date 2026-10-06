# infra-provisioning-api — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

`POST /stacks` validates a request and returns three Terraform files: `main.tf` calling `terraform/modules/service`, `variables.tf`, and `terraform.tfvars`. It also returns a monthly estimate for the chosen size. `applied` is false. Nothing here runs `terraform apply`, and GCP credentials are not read. The next step is a pull request.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/provision/main.py"]
    M1["src/provision/ops.py"]
    M2["src/provision/render.py"]
    M0 -->|imports| M1
    M0 -->|imports| M2
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/provision/main.py`](src/provision/main.py) | HTTP handlers: `GET /healthz`, `GET /options`, `POST /stacks` |
| [`src/provision/ops.py`](src/provision/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/provision/render.py`](src/provision/render.py) | Functions: `validate`, `render` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`terraform/modules/service/main.tf`](terraform/modules/service/main.tf) | Terraform resource/module declarations |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`tests/test_provision.py`](tests/test_provision.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

## Existing design and operating guides

These checked-in guides provide the project’s detailed design, operational context, or deployment view:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/provision/main.py`](src/provision/main.py#L21) |
| `GET /options` | `options` | [`src/provision/main.py`](src/provision/main.py#L26) |
| `POST /stacks` | `create_stack` | [`src/provision/main.py`](src/provision/main.py#L31) |
| `GET /readyz` | `readyz` | [`src/provision/ops.py`](src/provision/ops.py#L74) |
| `POST /workspaces` | `create_workspace` | [`src/provision/ops.py`](src/provision/ops.py#L80) |
| `GET /workspaces` | `list_workspaces` | [`src/provision/ops.py`](src/provision/ops.py#L98) |
| `POST /workspaces/{workspace_id}/jobs` | `create_job` | [`src/provision/ops.py`](src/provision/ops.py#L106) |
| `GET /jobs/{job_id}` | `get_job` | [`src/provision/ops.py`](src/provision/ops.py#L130) |
| `POST /jobs/{job_id}/approve` | `approve_job` | [`src/provision/ops.py`](src/provision/ops.py#L140) |
| `GET /audit` | `audit` | [`src/provision/ops.py`](src/provision/ops.py#L160) |
| `GET /metrics` | `metrics` | [`src/provision/ops.py`](src/provision/ops.py#L176) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `render(request)`

Source: [`src/provision/render.py`](src/provision/render.py#L39).

Calls visible in this function: `validate`.

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
    tfvars = (
        f'name         = "{request["name"]}"\n'
```

The excerpt is truncated; the linked source contains the full implementation.

### `validate(request)`

Source: [`src/provision/render.py`](src/provision/render.py#L20).

Calls visible in this function: `', '.join`, `LABEL.fullmatch`, `NAME.fullmatch`, `ORDER.index`, `RenderError`, `request.get`.

```python
def validate(request):
    if request["environment"] in {"prod", "production"}:
        raise RenderError("prod is not rendered; change the GitOps repository")
    if request["environment"] not in ENVIRONMENTS:
        raise RenderError("environment must be dev or staging")
    if not NAME.fullmatch(request["name"]):
        raise RenderError("name must be 3 to 30 lowercase letters, digits, or dashes, starting with a letter")
    if request["region"] not in REGIONS:
        raise RenderError(f"region must be one of {', '.join(REGIONS)}")
    if request["size"] not in SIZES:
        raise RenderError("size must be small, medium, or large")
    cap = SIZE_CAP[request["environment"]]
    if ORDER.index(request["size"]) > ORDER.index(cap):
        raise RenderError(f"{request['environment']} is capped at {cap}")
    for key in ("team", "cost_center"):
        if not LABEL.fullmatch(request.get(key) or ""):
            raise RenderError(f"{key} label is required: lowercase letters, digits, dashes, underscores")
```

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `HTTPException(status_code=422, detail=str(exc))` | [`src/provision/main.py`](src/provision/main.py#L35) |
| `HTTPException(status_code=404, detail='workspace not found')` | [`src/provision/ops.py`](src/provision/ops.py#L77) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/provision/ops.py`](src/provision/ops.py#L100) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/provision/ops.py`](src/provision/ops.py#L109) |
| `HTTPException(status_code=403, detail='production apply is disabled in this lab')` | [`src/provision/ops.py`](src/provision/ops.py#L113) |
| `RenderError('prod is not rendered; change the GitOps repository')` | [`src/provision/render.py`](src/provision/render.py#L22) |
| `RenderError('environment must be dev or staging')` | [`src/provision/render.py`](src/provision/render.py#L24) |
| `RenderError('name must be 3 to 30 lowercase letters, digits, or dashes, starting with a letter')` | [`src/provision/render.py`](src/provision/render.py#L26) |
| `RenderError(f"region must be one of {', '.join(REGIONS)}")` | [`src/provision/render.py`](src/provision/render.py#L28) |
| `RenderError('size must be small, medium, or large')` | [`src/provision/render.py`](src/provision/render.py#L30) |
| `RenderError(f"{request['environment']} is capped at {cap}")` | [`src/provision/render.py`](src/provision/render.py#L33) |
| `RenderError(f'{key} label is required: lowercase letters, digits, dashes, underscores')` | [`src/provision/render.py`](src/provision/render.py#L36) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/provision/ops.py`](src/provision/ops.py) defines module-level containers: `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`.
- [`src/provision/render.py`](src/provision/render.py) defines module-level containers: `SIZES`, `SIZE_CAP`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `render`

In [`src/provision/render.py`](src/provision/render.py#L39), `render(request)` receives the inputs. The function computes these intermediate values:

- `size = SIZES[request['size']]`
- `main = 'module "service" {\n  source       = "../../modules/service"\n  name         = var.name\n  environment  = var.environment\n  region       = var.region\n  machine_type = var.machine_type\n  labels       = var.labels\n}\n'`
- `variables = 'variable "name" { type = string }\nvariable "environment" { type = string }\nvariable "region" { type = string }\nvariable "machine_type" { type = string }\nvariable "labels" { type = map(string) }\n'`
- `tfvars = f'''name         = "{request['name']}"\nenvironment  = "{request['environment']}"\nregion       = "{request['region']}"\nmachine_type = "{size['machine_type']}"\nlabels = {{\n  team        = "{request['team']}"\n  cost_center = "{request['cost_center']}"\n  environment = "{request['environment']}"\n  managed_by  = "provisioning-api"\n}}\n'''`

Its result is defined by:

- `{'applied': False, 'estimate': {'machine_type': size['machine_type'], 'monthly_usd': size['monthly_usd']}, 'files': {'main.tf': main, 'variables.tf': variables, 'terraform.tfvars': tfvars}, 'next_step': 'Open a pull request with these files. A reviewed pipeline runs terraform plan and apply.'}`

### What does the operations plane add, and where is its limit

[`src/provision/ops.py`](src/provision/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_ops.py`](tests/test_ops.py), [`tests/test_provision.py`](tests/test_provision.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.
