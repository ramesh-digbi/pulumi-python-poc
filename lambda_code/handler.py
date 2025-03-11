import boto3
import os

INSTANCE_ID = os.environ["INSTANCE_ID"]
ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    action = event.get("rawPath", "").split("/")[-1]
    
    if action == "start":
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        return {"statusCode": 200, "body": f"Started EC2 {INSTANCE_ID}"}

    elif action == "stop":
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        return {"statusCode": 200, "body": f"Stopped EC2 {INSTANCE_ID}"}

    return {"statusCode": 400, "body": "Invalid action"}
