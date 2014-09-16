variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "aws_region" {
    default = "us-east-1"
}
variable "aws_amis" {
    default = {
        us-east-1 = "ami-7f418316"
        us-west-1 = "ami-951945d0"
    }
}

provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "${var.aws_region}"
}

resource "aws_security_group" "frontend" {
    name = "rzienertHttpSecurityGroup"
    description = "Enable HTTP traffic for frontend class servers"
    ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

resource "aws_elb" "frontend" {
    name = "rzienertFrontendLoadBalancer"
    availability_zones = ["#{aws_instance.frontend.availability_zone}"]

    listener {
        instance_port = 80
        instance_protocol = "http"
        lb_port = 80
        lb_protocol = "http"
    }

    instances = ["${aws_instance.frontend.id}"]
}

resource "aws_instance" "frontend" {
    instance_type = "t1.micro"
    ami = "${lookup(var.aws_amis, var.aws_region)}"
    security_groups = ["${aws_security_group.frontend.name}"]
    availability_zone = "us-east-1d"
}

output "InstanceId" {
    value = "${aws_instance.frontend.id}"
}

output "AZ" {
    value = "${aws_instance.frontend.availability_zone}"
}

output "PublicIP" {
    value = "${aws_instance.frontend.public_ip}"
}

output "PrivateIP" {
    value = "${aws_instance.frontend.private_ip}"
}

output "PublicDNS" {
    value = "${aws_elb.frontend.dns_name}"
}

output "PrivateDNS" {
    value = "${aws_instance.frontend.private_dns}"
}
