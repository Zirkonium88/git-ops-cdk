#!/usr/bin/env python3

from aws_cdk import App, Environment
from src.load_env.config import CDKConfig
from git_ops.git_ops_stack import GitOpsStack


class GitOpsSampleApp(App):
    """Create the CDK App.

    Args:
        App (aws_cdk.App): CDK App class
    """

    def __init__(self, *args, **kwargs):
        """Initialise this ensemble class."""
        super().__init__(*args, **kwargs)
        """Create the actual CloudFormation stack dependencies."""
        self.config = CDKConfig(self.node.try_get_context("environment"))
        self.default_env = Environment(
            account=self.config.get_value("AccountId"),
            region=self.config.get_value("AWSRegion"),
        )
        self.environment = self.node.try_get_context("environment")
        self.list_of_stacks = []
    
    def create_cfn_stacks(self):
        """Create CFN stacks."""
        sample_stack = GitOpsStack(
            self,
            construct_id="GitOpsStack",
            stack_name=f"mrht-{self.environment}-git-ops-stack",
            description=f"These stack create the {self.environment}",
            env=self.default_env,
            stage=self.config.get_value("Stage"),
        )
        self.list_of_stacks.append(sample_stack)


if __name__ == "__main__":
    app = GitOpsSampleApp()
    app.create_cfn_stacks()
    app.synth()