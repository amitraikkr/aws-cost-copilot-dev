# infra/cdk_constructs/lambdas.py
from __future__ import annotations
from typing import List, Optional, Dict

from aws_cdk import Duration, RemovalPolicy, Stack, aws_iam as iam, aws_logs as logs, aws_dynamodb as ddb, aws_lambda as _lambda
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct


class Lambdas(Construct):
    """
    Creates all Node.js Lambdas using the standard aws_lambda.Function
    (no esbuild, no lock files, no Docker bundling).

    Exposes:
      - self.health_fn
      - self.commands_fn
      - self.interactivity_fn
      - self.oauth_callback_fn
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_name: str,
        table: ddb.Table,
        secrets: Optional[Dict[str, secretsmanager.ISecret]] = None, 
        common_env: Optional[Dict[str, str]] = None,
        memory_mb: int = 256,
        timeout_sec: int = 5,
        log_retention_days: int = 14,
        project_root: str = "..",  
        layers: Optional[List[_lambda.ILayerVersion]] = None, 
    ) -> None:
        super().__init__(scope, construct_id)

        self.app_name = app_name
        self.env_name = env_name
        self.table = table
        self.secrets = secrets or {}
        self.common_env = {
            "APP_NAME": app_name,
            "ENV": env_name,
            "TABLE_NAME": table.table_name,
            **(common_env or {}),
        }
        self.memory_mb = memory_mb
        self.timeout_sec = timeout_sec
        self.log_retention_days = log_retention_days
        self.project_root = project_root
        self.layers = layers or []

        # Standard Lambda functions (no bundling)
        self.health_fn = self._create_fn(
            name="health",
            asset_dir=f"{project_root}/services/health",
            handler="src/index.handler",
        )
        self.commands_fn = self._create_fn(
            name="commands",
            asset_dir=f"{project_root}/services/commands",
            handler="src/index.handler",
        )
        self.interactivity_fn = self._create_fn(
            name="interactivity",
            asset_dir=f"{project_root}/services/interactivity",
            handler="src/index.handler",
        )
        self.oauth_callback_fn = self._create_fn(
            name="oauth_callback",
            asset_dir=f"{project_root}/services/oauth_callback",
            handler="src/index.handler",
        )

        # Grants (least privilege)
        for fn in [self.health_fn, self.commands_fn, self.interactivity_fn, self.oauth_callback_fn]:
            # DynamoDB single-table access
            self.table.grant_read_write_data(fn)

            for secret_name, secret in self.secrets.items():
                secret.grant_read(fn)

    def _create_fn(self, *, name: str, asset_dir: str, handler: str) -> _lambda.Function:
        fn_name = f"{self.app_name}-{name}-{self.env_name}"
        fn = _lambda.Function(
            self,
            f"{name.capitalize()}Function",
            function_name=fn_name,
            code=_lambda.Code.from_asset(asset_dir),  # zip the folder as-is
            handler=handler,                           # e.g., src/index.handler
            runtime=_lambda.Runtime.NODEJS_18_X,
            memory_size=self.memory_mb,
            timeout=Duration.seconds(self.timeout_sec),
            environment=self.common_env,
            log_retention=self._retention_enum(self.log_retention_days),
            architecture=_lambda.Architecture.ARM_64,  # cheaper; change to X86_64 if you prefer
            layers=self.layers,
        )

        # Clean up versions in dev to avoid clutter/cost
        fn.current_version.apply_removal_policy(RemovalPolicy.DESTROY)
        return fn

    @staticmethod
    def _retention_enum(days: int):
        mapping = {
            7: logs.RetentionDays.ONE_WEEK,
            14: logs.RetentionDays.TWO_WEEKS,
            30: logs.RetentionDays.ONE_MONTH,
            60: logs.RetentionDays.TWO_MONTHS,
            90: logs.RetentionDays.THREE_MONTHS,
        }
        return mapping.get(days, logs.RetentionDays.TWO_WEEKS)