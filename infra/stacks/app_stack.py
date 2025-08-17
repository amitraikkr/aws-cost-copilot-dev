# CDK app stack placeholder
# infra/stacks/app_stack.py
from __future__ import annotations
from typing import Optional, Dict, List

from aws_cdk import Stack, CfnOutput, Tags
from constructs import Construct

# Import your constructs
from cdk_constructs.dynamodb import DynamoTable
from cdk_constructs.kms_ssm import SecurityResources
from cdk_constructs.lambdas import Lambdas
from cdk_constructs.api import HttpApiConstruct
from cdk_constructs.layer import NodeDepsLayer

class AppStack(Stack):
    """
    Composes the serverless app:
      - DynamoDB (single-table)
      - Secrets Manager (secrets)
      - Node.js Lambdas (health, commands, interactivity, oauth_callback)
      - HTTP API (routes to Lambdas)

    Outputs:
      - ApiInvokeUrl
      - TableName
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str = "aws-cost-copilot",
        env_name: str = "dev",
        config: Optional[Dict] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # -------- Tagging (helps with cost allocation & discovery) --------
        Tags.of(self).add("App", app_name)
        Tags.of(self).add("Env", env_name)

        # -------- Config defaults (override via 'config' arg if you like) --------
        cfg = {
            "logRetentionDays": 14 if env_name.lower() == "dev" else 30,
            "lambdaMemoryMb": 256,
            "lambdaTimeoutSec": 5,
            "enableApiAccessLogs": True,
            "tableName": f"{app_name}-main-{env_name}",
            "slackSecretNames": [
                "slack/signing_secret",
                "slack/bot_token",
            ],
        }
        if config:
            cfg.update(config)

        # -------- DynamoDB --------
        db = DynamoTable(
            self,
            "Dynamo",
            app_name=app_name,
            env_name=env_name,
            table_name=cfg["tableName"],
            enable_pitr=True,
            ttl_attribute=None,   # add 'ttl' later if you want auto-expiry
            create_gsi1=True,
        )

        # -------- KMS + SSM (secrets) --------
        sec = SecurityResources(
            self,
            "Security",
            app_name=app_name,
            env_name=env_name,
            secret_names=cfg["slackSecretNames"],
            create_placeholders=True,
        )

        # -------- Node.js Layer --------
        node_layer = NodeDepsLayer(
            self,
            "NodeDepsLayer",
            app_name=app_name,
            env_name=env_name,
            project_root="..",
        )

        # -------- Lambdas --------
        lambdas = Lambdas(
            self,
            "Lambdas",
            app_name=app_name,
            env_name=env_name,
            table=db.table,
            secrets=sec.secrets,
            common_env={
                "LOG_LEVEL": "INFO",
            },
            memory_mb=cfg["lambdaMemoryMb"],
            timeout_sec=cfg["lambdaTimeoutSec"],
            log_retention_days=cfg["logRetentionDays"],
            project_root="..",  # repo root relative to /infra
            layers=[node_layer.layer],
        )

        # -------- HTTP API --------
        api = HttpApiConstruct(
            self,
            "HttpApi",
            app_name=app_name,
            env_name=env_name,
            health_fn=lambdas.health_fn,
            commands_fn=lambdas.commands_fn,
            interactivity_fn=lambdas.interactivity_fn,
            oauth_callback_fn=lambdas.oauth_callback_fn,
            enable_access_logs=False,
            log_retention_days=cfg["logRetentionDays"],
            stage_name="prod",
        )

        # -------- Outputs --------
        CfnOutput(self, "ApiInvokeUrl", value=api.invoke_url)
        CfnOutput(self, "TableName", value=db.table.table_name)

