from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
)


class GitOpsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        queue = sqs.Queue(
            self, "GitOpsQueue",
            visibility_timeout=Duration.seconds(300),
            queue_name=stage
        )

        topic = sns.Topic(
            self, "GitOpsTopic", topic_name=stage
        )

        topic.add_subscription(subs.SqsSubscription(queue))
