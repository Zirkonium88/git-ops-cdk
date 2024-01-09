#!/usr/bin/env python3

import aws_cdk as cdk

from git_ops.git_ops_stack import GitOpsStack


app = cdk.App()
GitOpsStack(app, "GitOpsStack")

app.synth()
