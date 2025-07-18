#!/usr/bin/env python3

import aws_cdk as cdk
from photo_app_stack import PhotoAppStack

app = cdk.App()
PhotoAppStack(app, "PhotoAppStack")

app.synth()