# Infrastructure provisioning API

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
