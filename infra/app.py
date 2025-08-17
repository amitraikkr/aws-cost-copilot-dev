# infra/app.py
from __future__ import annotations
import os
import aws_cdk as cdk
from aws_cdk import Environment

# Pipeline stack (CDK Pipelines)
from pipelines.pipeline_stack import AppCicdPipelineStack

APP_NAME = "aws-cost-copilot"


def main():
    app = cdk.App()

    # ---------- Resolve accounts/regions ----------
    dev_account = os.getenv("CDK_DEFAULT_ACCOUNT")
    dev_region = os.getenv("CDK_DEFAULT_REGION") or "us-east-1"
    dev_env = Environment(account=dev_account, region=dev_region)

    # Optional prod (set both PROD_ACCOUNT_ID and PROD_REGION to enable)
    prod_account = os.getenv("PROD_ACCOUNT_ID")
    prod_region = os.getenv("PROD_REGION")
    prod_env = (
        Environment(account=prod_account, region=prod_region)
        if prod_account and prod_region
        else None
    )

    # ---------- Source configuration (GitHub via CodeStar Connections) ----------
    # Expected environment variables (configure in your shell or CI):
    #   GITHUB_REPO            -> "owner/repo"
    #   GITHUB_BRANCH          -> "main" (default if not set)
    #   CODESTAR_CONNECTION_ARN-> arn:aws:codestar-connections:...:connection/uuid
    repo = os.getenv("GITHUB_REPO", "YOUR_GH_OWNER/YOUR_REPO")
    branch = os.getenv("GITHUB_BRANCH", "main")
    connection_arn = os.getenv("CODESTAR_CONNECTION_ARN", "")

    # ---------- Deploy the CI/CD pipeline (lives in the dev account/region) ----------
    AppCicdPipelineStack(
        app,
        f"{APP_NAME.capitalize().replace('-', '')}-Cicd",
        app_name=APP_NAME,
        dev_env=dev_env,
        prod_env=prod_env,
        repo_string=repo,
        branch=branch,
        connection_arn=connection_arn,
        env=dev_env,
        description=f"{APP_NAME} CDK Pipelines",
    )

    app.synth()


if __name__ == "__main__":
    main()