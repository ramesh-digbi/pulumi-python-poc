import pulumi
import pulumi_aws as aws
import json

# Replace with your existing EC2 instance ID
INSTANCE_ID = "i-0abcdef1234567890"

# IAM Role for Lambda Execution
lambda_role = aws.iam.Role("lambdaExecutionRole",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    })
)

# Attach necessary policies to allow Lambda to control EC2
aws.iam.RolePolicyAttachment("lambdaBasicExecution",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
)

aws.iam.RolePolicy("lambdaEC2Control",
    role=lambda_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["ec2:StartInstances", "ec2:StopInstances", "ec2:DescribeInstances"],
            "Resource": f"arn:aws:ec2:*:*:instance/{INSTANCE_ID}"
        }]
    })
)

# Define the Lambda function code
lambda_code = """
import json
import boto3
import os

INSTANCE_ID = os.getenv("INSTANCE_ID")
ec2_client = boto3.client("ec2")

def lambda_handler(event, context):
    action = event.get("action")
    if action == "start":
        ec2_client.start_instances(InstanceIds=[INSTANCE_ID])
        return {"status": "Instance started"}
    elif action == "stop":
        ec2_client.stop_instances(InstanceIds=[INSTANCE_ID])
        return {"status": "Instance stopped"}
    else:
        return {"status": "Invalid action"}
"""

# Create Lambda function for starting/stopping EC2
lambda_function = aws.lambda_.Function("ec2ControlLambda",
    role=lambda_role.arn,
    runtime="python3.9",
    handler="index.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.StringAsset(lambda_code)}),
    environment={
        "variables": {"INSTANCE_ID": INSTANCE_ID}
    },
    timeout=30
)

# Create API Gateway (HTTP API)
api_gateway = aws.apigatewayv2.Api("ec2Api",
    protocol_type="HTTP"
)

# Create API Gateway Integration for Lambda
integration = aws.apigatewayv2.Integration("lambdaIntegration",
    api_id=api_gateway.id,
    integration_type="AWS_PROXY",
    integration_uri=lambda_function.invoke_arn
)

# Create Start Route
start_route = aws.apigatewayv2.Route("startRoute",
    api_id=api_gateway.id,
    route_key="POST /start",
    target=pulumi.Output.concat("integrations/", integration.id)
)

# Create Stop Route
stop_route = aws.apigatewayv2.Route("stopRoute",
    api_id=api_gateway.id,
    route_key="POST /stop",
    target=pulumi.Output.concat("integrations/", integration.id)
)

# Deploy API Gateway
deployment = aws.apigatewayv2.Deployment("apiDeployment",
    api_id=api_gateway.id
)

# Create Stage
stage = aws.apigatewayv2.Stage("apiStage",
    api_id=api_gateway.id,
    name="prod",
    deployment_id=deployment.id
)

# Permission for API Gateway to invoke Lambda
permission = aws.lambda_.Permission("apiGatewayInvokeLambda",
    action="lambda:InvokeFunction",
    function=lambda_function.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(api_gateway.execution_arn, "/*/*")
)

# Export API Gateway endpoint
pulumi.export("api_url", pulumi.Output.concat(stage.invoke_url))
