# infra/stages/app_stage.py
from __future__ import annotations
import aws_cdk as cdk
from constructs import Construct
from stacks.app_stack import AppStack

class AppStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, *, app_name: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        AppStack(
            self,
            f"{app_name.capitalize().replace('-','')}-App-{env_name}",
            app_name=app_name,
            env_name=env_name,
            description=f"{app_name} app ({env_name})",
        )