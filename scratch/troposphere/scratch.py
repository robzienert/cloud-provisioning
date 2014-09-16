import boto
import boto.cloudformation
from troposphere import Base64, FindInMap, GetAtt, GetAZs
from troposphere import Parameter, Output, Ref, Template
import troposphere.ec2 as ec2
import troposphere.elasticloadbalancing as elb
import argparse

t = Template()

t.add_mapping("RegionMap", {
    "us-east-1": {"AMI": "ami-7f418316"},
    "us-west-1": {"AMI": "ami-951945d0"}
})

# Add a frontend tag?
frontend_ec2_sg = t.add_resource(ec2.SecurityGroup(
    "rzienertHttpSecurityGroup",
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
    "rzienertInstance",
    ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
    InstanceType="t1.micro",
    SecurityGroups=[Ref(frontend_ec2_sg)],
    UserData=Base64("80")
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
args = parser.parse_args()

conn = boto.cloudformation.connect_to_region(
    "us-east-1", 
    aws_access_key_id=args.access_key, 
    aws_secret_access_key=args.secret_key)
stack_id = conn.create_stack(
    "rzienertTroposphereTest",
    template_body=t.to_json())
print(stack_id)
