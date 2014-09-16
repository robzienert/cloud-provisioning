# Cloud Provisioning Scratches

* Create a basic AWS topology: 
    * ASG
    * SG
    * EC2 instance from image
    * Output
        * InstanceID
        * AZ
        * PublicIP
        * PrivateIP
        * PublicDNS
        * PrivateDNS
* Should create a static state file (in whatever form that is; CloudFormation or otherwise)

## Implementations

* Troposphere: https://github.com/cloudtools/troposphere
* Terraform: http://terraform.io
