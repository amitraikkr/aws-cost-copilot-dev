# infra/pipelines/pipeline_stack.py
from __future__ import annotations
import aws_cdk as cdk
from aws_cdk import pipelines as pipelines
from constructs import Construct
from stages.app_stage import AppStage

class AppCicdPipelineStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        dev_env: cdk.Environment,
        prod_env: cdk.Environment | None,
        repo_string: str,            # "owner/repo"
        branch: str = "main",
        connection_arn: str = "",    # CodeStar Connection ARN
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source = pipelines.CodePipelineSource.connection(
            repo_string,
            branch,
            connection_arn=connection_arn,
        )

        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            commands=[
                "pip install --upgrade pip",
                "pip install -r infra/requirements.txt",
                "cd infra",
                "cdk synth --context env=dev"  # synth template; stage envs handled below
            ],
            primary_output_directory="infra/cdk.out",
        )

        pipe = pipelines.CodePipeline(
            self,
            "Pipeline",
            pipeline_name=f"{app_name}-cicd",
            synth=synth_step,
        )

        # DEV stage
        dev_stage = AppStage(
            self,
            "Dev",
            app_name=app_name,
            env_name="dev",
            env=dev_env,
        )
        pipe.add_stage(dev_stage)

        # Optional: manual approval before prod
        if prod_env:
            pipe.add_wave("Approve").add_post(pipelines.ManualApprovalStep("PromoteToProd"))
            prod_stage = AppStage(
                self,
                "Prod",
                app_name=app_name,
                env_name="prod",
                env=prod_env,
            )
            pipe.add_stage(prod_stage)