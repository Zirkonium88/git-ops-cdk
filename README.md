# GitOps with the Cloud Development Kit (CDK) in Python

## TLDR;

By using the `--context` flag of the CDK CLI and a bit of Python code, a JSON file can be read in, which enables dynamic deployments via Azure DevOps and similar systems from the GUI by using parameters.

## Intro

AWS recommends using different environments for building IT systems. There are various reasons for doing this, for example the better use of service quotas or the reduction of risks.

Linear staging is often used for this purpose. A development environment is followed by a similar acceptance environment, which is followed by a production environment. One problem that arises is how to duplicate environments while keeping costs and benefits in mind.

It may be the case, that you don't want a strictly linear or even fully automated infrastructure setup of similar environments. This can be the case, for example, in a PoCs.

Regardless of whether you deploy fully or partially automated, infrastructure as code (IaC) helps a lot because this is how uniformity can be created. If the code can also be parameterized and thus become dynamic, this contributes to the cost efficiency of the systems.

With the appropriate parameterization, the CDK can be used to create a partially automated environments via IaC with the help of GitOps. GitOps is a concept that aims to further automate IT operations. An important core component is the fully declarative and versioned target state defined in Git.

## Definition of Environments via Config Files

This example uses the CDK sample app, which was created via `cdk init sample-app --language=python`. This app creates resources, a SNS topic and a SQS queue, which can operate with each other via the AWS API.

To keep the example simple, our GitOps approach only involves changing the name of the resource and the account.

To do this, I created two JSON files under `./config/..` in the repository:

```JSON
# developing.json
{
    "AccountId": "1234567891011",
    "AWSRegion": "eu-central-1",
    "Stage": "developing" # changed in production.json accordingly
}
```

The CDK now makes it possible to work with these files in all languages. In Python, my example code for loading the JSON files looks like the following:

```Python
# ./src/load_env/config.py

import json
import logging

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] - %(message)s", force=True
)

class CDKConfig:
    """Generate CDK config object for multi environment deployments."""

    def __init__(self, environment: str) -> None:
        """Initialize config object.

        Args:
            environment (str): name of the environment. Need to be in line with names of JSON config files.
        """
        self._environment = environment
        self.load_config()

    def load_config(self) -> dict:
        """Load the config object.

        Returns:
            dict:  json config object
        """
        with open(f"config/{self._environment}.json") as json_inline:
            self.data = json.load(json_inline)
        return self.data

    def get_value(self, key: str) -> str:
        """Get value from config object.

        Args:
            key (str): name of the key to the key-value pair

        Returns:
            str: value of the key-value-pair
        """
        try:
            return self.data[key]
        except KeyError as e:
            logging.error(e)
            logging.error(self.data)
```

The code creates a Python class that first loads the corresponding JSON file. These are identified via the environment name. Afterwards, the entire JSON file can be returned as a Python dictionary or individual values.

## Using Config files based on Environments

To address the different environments with the CDK, you can use the environment flag: `cdk deploy --all --ci --require-approval never --context environment=developing`.

In the app.py, the CDK execution file, the value can be captured as follows:

```Python
# ./app.py

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
```

The GitOpsSampleApp class is initialized with the class from the `./src/load_env/config.py` files. `self.config = CDKConfig(self.node.try_get_context("environment"))` gives me access to the contents of the JSON file, while `self.environment = self.node.try_get_context("environment")`. The rest of the `app.py` file is my personal style and can be designed in any other way.

If the environments are in the same AWS account, it is helpful to also define the CloudFormation stack name with `self.environment`, as shown in the `create_cfn_stacks()` function.

Ultimately, the values (here `stage`) in the `./git_ops/git_ops_
stack.py` files can then be used:

```Python
# /git_ops/git_ops_stack.py

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

```

Using the `stage` variable of the GitOpsStack class, we can now name the resources according to the environment.

## GitOps via Azure DevOps and others

In my case, the final step now takes place via Azure DevOps. Parameters are defined in the pipeline definition below. Those parameters sets can now be used to start the pipeline manually. Two different service connections define the different accounts for production and development. Service connections hold credentials to interact with AWS API. The `AwsRegion` parameter is set to eu-central-1, but can also be set differently per environment. Finally, the `environmentName` parameter is the important one to be used to address different environments via CDK.

```YAML
trigger:
- none

parameters:
- name: ServiceConnection
  displayName: Service Connection
  type: string
  default: developing-aws-service-endpoint
  values:
    - developing-aws-service-endpoint
    - production-aws-service-endpoint
- name: AwsRegion
  displayName: AWS Region
  type: string
  default: eu-central-1
- name: environmentName
  type: string
  default: developing
  values:
    - developing
    - production

pool:
  name: BuildAgents
  vmImage: 'ubuntu-latest'

stages:
- stage: '${{ parameters.environmentName }}'
  displayName: DeployStage-${{ parameters.environmentName }}
  jobs:
  - job: DeployApp
    steps:
    - template: azure-pipelines-common.yml
    - task: AWSShellScript@1
      inputs:
        awsCredentials: ${{ parameters.ServiceConnection }}
        regionName: ${{ parameters.AwsRegion }}
        scriptType: 'inline'
        inlineScript: |
          echo "Deploying App in "${{ parameters.environmentName }} $AWS_DEFAULT_REGION
          cdk deploy -ci --require-approval never --context environment=${{ parameters.environmentName }}
      displayName: 'Deploying CDK app'
```

The GitOps-based deployment via the CDK then looks like this and can be started from the Azure DevOps GUI: `cdk deploy -ci --require-approval never --context environment=${{ parameters.environmentName }}` by selecting the correct parameter values.

The flags `--ci` and `--require-approval never` ensure that the deployment runs without approval.

## Summary

With the CDK, GitOps-based deployments can be easily implemented. A high level of flexibility can be achieved with little additional work. The example shows how to use Azure DevOps, but I have already done something similar with GitLab, so that it can easily be transferred to other systems. Whether a GitOps approach makes sense depends on the individual use case.

