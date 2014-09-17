import boto
import boto.cloudformation
from troposphere import Base64, FindInMap, GetAtt, GetAZs
from troposphere import Parameter, Output, Ref, Template, Tags, Join
import troposphere.ec2 as ec2
import troposphere.elasticloadbalancing as elb
import argparse

# Depends on already created VPC.

t = Template()

vpcid_param = t.add_parameter(Parameter(
    "VpcId",
    Description="VpcId of the existing VPC",
    Type="String"
))

subnetid_param = t.add_parameter(Parameter(
    "SubnetId",
    Description="SubnetId of an existing subnet (for the primary network) in the VPC",
    Type="String"
))

t.add_mapping("RegionMap", {
    "us-east-1": {"AMI": "ami-7f418316"},
    "us-west-1": {"AMI": "ami-951945d0"}
})

# TODO: Not being added to the VPC? EC2 instance creation fails saying the SG isn't part
#       of the VPC? ...
frontend_ec2_sg = t.add_resource(ec2.SecurityGroup(
    "rzienertHttpSecurityGroup",
    VpcId=Ref(vpcid_param),
    GroupDescription="Enable HTTP traffic for frontend class servers",
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="80",
            ToPort="80",
            CidrIp="0.0.0.0/0"
        )
    ]
))

ec2_instance = t.add_resource(ec2.Instance(
    "rzienertEC2Instance",
    ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
    SecurityGroups=[Ref(frontend_ec2_sg)],
    Tags=Tags(Name="rzienertVpcInstance")
))

elb = t.add_resource(elb.LoadBalancer(
    "rzienertLoadBalancer",
    AvailabilityZones=GetAZs(""),
    ConnectionDrainingPolicy=elb.ConnectionDrainingPolicy(
        Enabled=True,
        Timeout=300
    ),
    CrossZone=True,
    Instances=[Ref(ec2_instance)],
    Listeners=[
        elb.Listener(
            LoadBalancerPort="80",
            InstancePort="80",
            Protocol="HTTP"
        )
    ],
    HealthCheck=elb.HealthCheck(
        Target="HTTP:80/",
        HealthyThreshold="3",
        UnhealthyThreshold="5",
        Interval="30",
        Timeout="5"
    )
))

t.add_output([
    Output(
        "InstanceId",
        Value=Ref(ec2_instance)
    ),
    Output(
        "AZ",
        Value=GetAtt(ec2_instance, "AvailabilityZone")
    ),
    Output(
        "PublicIP",
        Value=GetAtt(ec2_instance, "PublicIp")
    ),
    Output(
        "PrivateIP",
        Value=GetAtt(ec2_instance, "PrivateIp")
    ),
    Output(
        "PublicDNS",
        Value=GetAtt(elb, "DNSName")
    ),
    Output(
        "PrivateDNS",
        Value=GetAtt(ec2_instance, "PrivateDnsName")
    )
])

parser = argparse.ArgumentParser()
parser.add_argument("--access-key")
parser.add_argument("--secret-key")
parser.add_argument("--vpc-id")
parser.add_argument("--subnet-id")
args = parser.parse_args()

conn = boto.cloudformation.connect_to_region(
    "us-east-1", 
    aws_access_key_id=args.access_key, 
    aws_secret_access_key=args.secret_key)

stack_id = conn.create_stack(
    "rzienertVpcTroposphereTest",
    template_body=t.to_json(),
    parameters=[
        ("VpcId", args.vpc_id),
        ("SubnetId", args.subnet_id)
    ]
)
print(stack_id)
