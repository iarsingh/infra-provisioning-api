# Infrastructure provisioning API

Level: Intermediate

Skills: FastAPI, Terraform, GCP-ready layout, infrastructure as code

`POST /stacks` returns a Terraform file that calls `terraform/modules/service`. The module rejects `prod` in its own validation block. The API sets `applied` to false. Nothing here runs `terraform apply`, and GCP credentials are not read.

```bash
pip install -r requirements.txt
pytest -q
terraform -chdir=terraform/modules/service init -backend=false
terraform -chdir=terraform/modules/service validate
```

