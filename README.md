# Infrastructure provisioning API

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/provision/main.py`](src/provision/main.py) | HTTP handlers: `GET /healthz`, `GET /options`, `POST /stacks` |
| [`src/provision/render.py`](src/provision/render.py) | Functions: `validate`, `render` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`terraform/modules/service/main.tf`](terraform/modules/service/main.tf) | Terraform resource/module declarations |
| [`tests/test_provision.py`](tests/test_provision.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn provision.main:app --reload
```

<!-- project-guide:end -->

Level: Intermediate

Skills: FastAPI, Terraform, GCP-ready layout, infrastructure as code, input validation

`POST /stacks` validates a request and returns three Terraform files: `main.tf` calling `terraform/modules/service`, `variables.tf`, and `terraform.tfvars`. It also returns a monthly estimate for the chosen size. `applied` is false. Nothing here runs `terraform apply`, and GCP credentials are not read. The next step is a pull request.

```bash
pip install -r requirements.txt
pytest -q
terraform -chdir=terraform/modules/service init -backend=false
terraform -chdir=terraform/modules/service validate
PYTHONPATH=src uvicorn provision.main:app --reload
```

```bash
curl -s -X POST localhost:8000/stacks -H 'content-type: application/json' -d '{
  "name": "billing", "environment": "dev", "region": "us-central1",
  "size": "small", "team": "payments", "cost_center": "cc_104"
}'
```

| Size | Machine type | Estimate per month |
| --- | --- | --- |
| small | e2-small | 13 USD |
| medium | e2-standard-2 | 49 USD |
| large | e2-standard-4 | 98 USD |

`GET /options` lists the allowed regions, sizes, and caps.

## What it refuses

- `prod`. Production is a reviewed change in the GitOps repository.
- A name that is not 3 to 30 lowercase letters, digits, or dashes. User input is never pasted into HCL unchecked, so a quote cannot inject a new `source`.
- A region outside `us-central1`, `europe-west1`, `asia-south1`.
- `large` in dev. Dev is capped at medium; staging allows large.
- A missing `team` or `cost_center` label.

The module repeats the same rules in its own `validation` blocks, so a hand-edited `tfvars` file fails `terraform validate` or `plan` for the same reasons the API refuses it.

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.
