# infra/app.py
from __future__ import annotations
import os
import aws_cdk as cdk
from aws_cdk import Environment

# import your real application stack (the one that created API/Lambdas/Dynamo/etc.)
from stacks.app_stack import AppStack

APP_NAME = "aws-cost-copilot"

def main():
    app = cdk.App()

    # Envs (dev default)
    dev_account = os.getenv("CDK_DEFAULT_ACCOUNT")
    dev_region = os.getenv("CDK_DEFAULT_REGION", "us-west-2")
    dev_env = Environment(account=dev_account, region=dev_region)

    # Deploy only the app (no pipelines)
    AppStack(
        app,
        f"{APP_NAME.capitalize().replace('-', '')}-App-dev",
        env=dev_env,
        description=f"{APP_NAME} application (dev)",
    )

    app.synth()

if __name__ == "__main__":
    main()