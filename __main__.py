import pulumi
import pulumi_aws as aws

vpc_id = "vpc-08f7f42000b5f316e"

# Get all subnets in the specified VPC
subnets = aws.ec2.get_subnets(filters=[{"name": "vpc-id", "values": [vpc_id]}])

# Pick the first available subnet (modify if needed)
subnet_id = subnets.ids[0] if subnets.ids else None

if not subnet_id:
    raise ValueError("No subnet found in the specified VPC!")

# Define a Security Group for the instance
security_group = aws.ec2.SecurityGroup("sgForPulumiTestEc2Instance",
    vpc_id=vpc_id,
    description="Allow SSH and HTTP access",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},  # SSH
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},  # HTTP
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},  # Allow all outbound
    ]
)

# Get the latest Ubuntu AMI (20.04 LTS in this case)
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical (Ubuntu) official AWS account ID
    filters=[{"name": "name", "values": ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]}]
)

# Choose an Amazon Machine Image (AMI)
#ami = aws.ec2.get_ami(most_recent=True,
#    owners=["amazon"],  # Official Amazon AMIs
#    filters=[{"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
#)

# Create the EC2 Instance
instance = aws.ec2.Instance("myEC2UbuntuForStartStopTest",
    instance_type="t2.micro",  # Free-tier eligible
    ami=ami.id,
    key_name="pulumi-test",
    subnet_id=subnet_id,
    vpc_security_group_ids=[security_group.id],
    associate_public_ip_address=True,
    tags={
        "Name": "PulumiEC2Instance"
    }
)

# Get the first attached volume (modify if you have multiple volumes)
volume_id = instance.root_block_device[0].volume_id  # Root volume


# Export the instance public IP and ID
pulumi.export("instance_id", instance.id)
pulumi.export("public_ip", instance.public_ip)
pulumi.export("availability_zone",instance.availability_zone)
pulumi.export("subnet_id",subnet_id)
# Export snapshot details
#pulumi.export("snapshot_id", snapshot.id)
#pulumi.export("snapshot_volume", snapshot.volume_id)