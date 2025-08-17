# infra/constructs/api.py
from __future__ import annotations
from typing import Optional

from aws_cdk import Duration, aws_apigatewayv2 as apigwv2, aws_apigatewayv2_integrations as integrations, aws_logs as logs
from constructs import Construct
from aws_cdk.aws_lambda import IFunction


class HttpApiConstruct(Construct):
    """
    Provisions a low-cost HTTP API and wires Lambda routes:
      - GET  /health            -> health_fn
      - POST /slack/commands    -> commands_fn
      - POST /slack/interactivity-> interactivity_fn
      - GET  /auth/slack/callback-> oauth_callback_fn

    Exposes:
      - self.api (apigwv2.HttpApi)
      - self.stage (apigwv2.HttpStage)
      - self.invoke_url (str)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_name: str,
        health_fn: IFunction,
        commands_fn: IFunction,
        interactivity_fn: IFunction,
        oauth_callback_fn: IFunction,
        enable_access_logs: bool = True,
        log_retention_days: int = 14,
        stage_name: str = "prod",
    ) -> None:
        super().__init__(scope, construct_id)

        name = f"{app_name}-api-{env_name}"

        # HTTP API
        self.api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name=name,
            description=f"{app_name} public HTTP API ({env_name})",
            cors_preflight=None,  # Slack posts; no browser CORS needed for MVP
        )

        # Access logs (optional but recommended)
        self.stage = apigwv2.HttpStage(
            self,
            "HttpApiStage",
            http_api=self.api,
            stage_name=stage_name,
            auto_deploy=True,
        )

        # Integrations
        health_int = integrations.HttpLambdaIntegration("HealthInt", health_fn)
        commands_int = integrations.HttpLambdaIntegration("CommandsInt", commands_fn)
        interactivity_int = integrations.HttpLambdaIntegration("InteractivityInt", interactivity_fn)
        oauth_cb_int = integrations.HttpLambdaIntegration("OauthCbInt", oauth_callback_fn)

        # Routes
        self.api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=health_int,
        )
        self.api.add_routes(
            path="/slack/commands",
            methods=[apigwv2.HttpMethod.POST],
            integration=commands_int,
        )
        self.api.add_routes(
            path="/slack/interactivity",
            methods=[apigwv2.HttpMethod.POST],
            integration=interactivity_int,
        )
        self.api.add_routes(
            path="/auth/slack/callback",
            methods=[apigwv2.HttpMethod.GET],
            integration=oauth_cb_int,
        )

        self.invoke_url = f"{self.api.api_endpoint}/{self.stage.stage_name}"