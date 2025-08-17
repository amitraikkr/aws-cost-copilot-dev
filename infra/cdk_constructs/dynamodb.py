# infra/constructs/dynamodb.py
from __future__ import annotations
from typing import Optional

from aws_cdk import RemovalPolicy, Duration, aws_dynamodb as ddb
from constructs import Construct


class DynamoTable(Construct):
    """
    Provisions the single-table DynamoDB used by aws-cost-copilot.

    - On-demand billing (cheap to start, scales automatically)
    - pk / sk keys (string)
    - Optional TTL attribute
    - Optional GSI1 (gsi1pk / gsi1sk) for future queries (e.g., scheduling)
    - PITR enabled by default
    - Removal policy: DESTROY in dev, RETAIN otherwise

    Exposes:
      - self.table (aws_cdk.aws_dynamodb.Table)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_name: str,
        table_name: Optional[str] = None,
        enable_pitr: bool = True,
        ttl_attribute: Optional[str] = None,
        create_gsi1: bool = True,
        point_read_capacity: Optional[int] = None,  # reserved for future switch to provisioned if needed
        point_write_capacity: Optional[int] = None,
    ) -> None:
        super().__init__(scope, construct_id)

        name = table_name or f"{app_name}-main-{env_name}"
        removal = RemovalPolicy.DESTROY if env_name.lower() == "dev" else RemovalPolicy.RETAIN

        self.table = ddb.Table(
            self,
            "MainTable",
            table_name=name,
            partition_key=ddb.Attribute(name="pk", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="sk", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=enable_pitr,
            time_to_live_attribute=ttl_attribute,
            removal_policy=removal,
            # Server-side encryption is on by default with AWS owned key; can switch to CMK later if required.
        )

        if create_gsi1:
            self.table.add_global_secondary_index(
                index_name="GSI1",
                partition_key=ddb.Attribute(name="gsi1pk", type=ddb.AttributeType.STRING),
                sort_key=ddb.Attribute(name="gsi1sk", type=ddb.AttributeType.STRING),
                projection_type=ddb.ProjectionType.ALL,
            )

        # Recommended default TTL attribute (you can pass a different one above)
        if ttl_attribute is None:
            # Not enabling TTL when attribute is None, but documenting a default you can adopt later:
            # e.g., store 'ttl' epoch seconds on items you want auto-expired.
            pass

    @property
    def name(self) -> str:
        return self.table.table_name