# infra/cdk_constructs/kms_ssm.py
from __future__ import annotations
from typing import Optional, List, Dict

from aws_cdk import RemovalPolicy, SecretValue, aws_secretsmanager as sm
from constructs import Construct


class SecurityResources(Construct):
    """
    Secrets-only (Secrets Manager) construct:
      - Creates named secrets under /<app>/<env>/...
      - No customer-managed KMS key
      - Dev: DESTROY on stack delete; Prod: RETAIN

    Exposes:
      - self.secrets: Dict[str, sm.Secret]
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_name: str,
        secret_names: Optional[List[str]] = None,   # e.g. ["slack/signing_secret", "slack/bot_token"]
        create_placeholders: bool = True,           # create with "PLACEHOLDER" so stack can deploy
    ) -> None:
        super().__init__(scope, construct_id)

        removal = RemovalPolicy.DESTROY if env_name.lower() == "dev" else RemovalPolicy.RETAIN
        secret_names = secret_names or ["slack/signing_secret", "slack/bot_token"]

        self.secrets: Dict[str, sm.Secret] = {}

        for name in secret_names:
            secret_path = f"/{app_name}/{env_name}/{name}".replace("//", "/")
            # Create a simple string secret; you will overwrite with real values after deploy.
            secret = sm.Secret(
                self,
                f"{name.replace('/','_').replace('-','_').capitalize()}Secret",
                secret_name=secret_path,
                secret_string_value=SecretValue.unsafe_plain_text("PLACEHOLDER") if create_placeholders
                                     else SecretValue.unsafe_plain_text(""),
                description=f"{app_name} secret ({env_name}) for {name}",
            )
            secret.apply_removal_policy(removal)
            self.secrets[name] = secret