import re

NAME = re.compile(r"^[a-z][a-z0-9-]{1,28}[a-z0-9]$")
LABEL = re.compile(r"^[a-z0-9_-]{1,63}$")
ENVIRONMENTS = ("dev", "staging")
REGIONS = ("us-central1", "europe-west1", "asia-south1")
SIZES = {
    "small": {"machine_type": "e2-small", "monthly_usd": 13},
    "medium": {"machine_type": "e2-standard-2", "monthly_usd": 49},
    "large": {"machine_type": "e2-standard-4", "monthly_usd": 98},
}
SIZE_CAP = {"dev": "medium", "staging": "large"}
ORDER = ("small", "medium", "large")


class RenderError(ValueError):
    pass


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
        f'environment  = "{request["environment"]}"\n'
        f'region       = "{request["region"]}"\n'
        f'machine_type = "{size["machine_type"]}"\n'
        "labels = {\n"
        f'  team        = "{request["team"]}"\n'
        f'  cost_center = "{request["cost_center"]}"\n'
        f'  environment = "{request["environment"]}"\n'
        '  managed_by  = "provisioning-api"\n'
        "}\n"
    )
    return {
        "applied": False,
        "estimate": {"machine_type": size["machine_type"], "monthly_usd": size["monthly_usd"]},
        "files": {"main.tf": main, "variables.tf": variables, "terraform.tfvars": tfvars},
        "next_step": "Open a pull request with these files. A reviewed pipeline runs terraform plan and apply.",
    }
