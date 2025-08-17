# infra/cdk_constructs/layer.py
from __future__ import annotations
from aws_cdk import RemovalPolicy, aws_lambda as _lambda
from constructs import Construct

class NodeDepsLayer(Construct):
    """
    Packages a Node.js 18 Lambda Layer from layers/shared-node18/nodejs
    to share npm deps and optional shared JS across functions.
    """
    def __init__(self, scope: Construct, construct_id: str, *, app_name: str, env_name: str, project_root: str = "..") -> None:
        super().__init__(scope, construct_id)

        self.layer = _lambda.LayerVersion(
            self,
            "SharedNode18Layer",
            layer_version_name=f"{app_name}-node18-{env_name}",
            code=_lambda.Code.from_asset(f"{project_root}/layers/shared-node18"),
            compatible_runtimes=[_lambda.Runtime.NODEJS_18_X],
            description=f"{app_name} shared Node.js 18 deps ({env_name})"
        )
        # Safe to destroy in dev, retain in prod if you prefer
        self.layer.apply_removal_policy(RemovalPolicy.DESTROY if env_name.lower() == "dev" else RemovalPolicy.RETAIN)