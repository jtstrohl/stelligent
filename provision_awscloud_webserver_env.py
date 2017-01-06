import argparse
import time
import boto3
import botocore
from troposphere import Base64, GetAtt, Join, Output, Ref, Tags, Template
from troposphere.ec2 import Instance, InternetGateway, NetworkAcl, \
    NetworkAclEntry, NetworkInterfaceProperty, PortRange, Route, \
    RouteTable, SecurityGroup, SecurityGroupRule, Subnet, \
    SubnetNetworkAclAssociation, SubnetRouteTableAssociation, VPC, \
    VPCGatewayAttachment


# Define some constants to use
# TODO: Consider passing the following values in as optional command line args
VPC_CIDR = '10.0.0.0/16'
SUBNET_CIDR = '10.0.0.0/24'
PROJECT = 'Jonathan Strohl\'s Mini-Project'
NAME_PREFIX = 'jstrohl-miniproject-'
STACK_NAME = NAME_PREFIX + 'stack'

# TODO: Consider adding more supported regions, in addition to US
supported_regions_ami_map = {
                             'us-east-1' : 'ami-b73b63a0',
                             'us-east-2' : 'ami-58277d3d',
                             'us-west-1' : 'ami-23e8a343',
                             'us-west-2' : '8mi-5ec1673e'
                            }

def provision_environment(id, secret, key_pair, region, type_instance):
    """ Provision the web server cloud environment """
    
    validate_key_pair(id, secret, key_pair, region)
    template = create_template(key_pair, region, type_instance)
    create_stack(id, secret, key_pair, region, template)


def validate_key_pair(id, secret, key_pair, region):
    """ Make sure the specified key pair exists in the specified region """

    # Create boto3 client for AWS EC2
    client = boto3.client('ec2',
                          aws_access_key_id=id,
                          aws_secret_access_key=secret,
                          region_name=region)

    # Look for specified AWS key pair in this region
    try:
        kp = client.describe_key_pairs(KeyNames=[key_pair])
    except:
        print '\n"%s" is not an existing key pair in AWS Region "%s".' % (key_pair, region)
        print 'Select an existing key pair defined in your AWS Account for this region.\n'
        exit(0)


def create_template(key_pair, region, type_instance):
    """ Create the Cloud Formation Template """

    # Create references for the CFT
    ref_stack_id = Ref('AWS::StackId')
    ref_region = Ref('AWS::Region')
    ref_stack_name = Ref('AWS:StackName')

    # Add the template header
    t = Template()
    t.add_version('2010-09-09')
    t.add_description(PROJECT + ": " +\
        'AWS Cloud Formation Template for creating a custom VPC with '\
        'public subnet to host a simple web server on a single EC2 instance '\
        'with a security group that allows public HTTP and SSH traffic.')

    # Add the VPC
    vpc = t.add_resource(
        VPC(
            'VPC',
            CidrBlock=VPC_CIDR,
            Tags=Tags(
                Application=ref_stack_id,
                Name=NAME_PREFIX+'vpc',
                Project=PROJECT)))

    # Add a public Subnet for our web server
    public_subnet = t.add_resource(
        Subnet(
            'Subnet',
            CidrBlock=SUBNET_CIDR,
            VpcId=Ref(vpc),
            Tags=Tags(
                Application=ref_stack_id,
                Name=NAME_PREFIX+'public-subnet',
                Project=PROJECT)))

    # Add an IGW for public access
    internet_gateway = t.add_resource(
        InternetGateway(
            'InternetGateway',
            Tags=Tags(
                Application=ref_stack_id,
                Name=NAME_PREFIX+'igw',
                Project=PROJECT)))

    # Attach our IGW to our VPC
    gateway_attachment = t.add_resource(
        VPCGatewayAttachment(
            'AttachGateway',
            VpcId=Ref(vpc),
            InternetGatewayId=Ref(internet_gateway)))

    # Add a custom Route Table for public access
    route_table = t.add_resource(
        RouteTable(
            'RouteTable',
            VpcId=Ref(vpc),
            Tags=Tags(
                Application=ref_stack_id,
                Name=NAME_PREFIX+'publicroutetable',
                Project=PROJECT)))
            
    # Add a public Route to our Route Table through our IGW
    public_route = t.add_resource(
        Route(
            'Route',
            DependsOn='AttachGateway',
            GatewayId=Ref(internet_gateway),
            DestinationCidrBlock='0.0.0.0/0',
            RouteTableId=Ref(route_table)))

    # Associate our public Subnet with our public Route Table
    subnet_route_table_assoc = t.add_resource(
        SubnetRouteTableAssociation(
            'SubnetRouteTableAssociation',
            SubnetId=Ref(public_subnet),
            RouteTableId=Ref(route_table)))

    # Add a new Network ACL for our public Subnet
    network_acl = t.add_resource(
        NetworkAcl(
            'NetworkAcl',
            VpcId=Ref(vpc),
            Tags=Tags(
                Application=ref_stack_id,
                Name=NAME_PREFIX+'networkacl',
                Project=PROJECT)))

    # Inbound ACL Rule for HTTP
    inboundHttpAclEntry = t.add_resource(
        NetworkAclEntry(
            'InboundHTTPNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='100',
            Protocol=6,
            PortRange=PortRange(To='80', From='80'),
            Egress='false',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Inbound ACL Rule for HTTPS
    inboundHttpsAclEntry = t.add_resource(
        NetworkAclEntry(
            'InboundHTTPSNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='200',
            Protocol=6,
            PortRange=PortRange(To='443', From='443'),
            Egress='false',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Inbound ACL Rule for SSH
    inboundSshAclEntry = t.add_resource(
        NetworkAclEntry(
            'InboundSSHNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='300',
            Protocol=6,
            PortRange=PortRange(To='22', From='22'),
            Egress='false',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Inbound ACL Rule for Ephemeral Response Ports
    inboundResponsePortsAclEntry = t.add_resource(
        NetworkAclEntry(
            'InboundResponsePortsNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='400',
            Protocol=6,
            PortRange=PortRange(To='65535', From='1024'),
            Egress='false',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Outbound ACL Rule for HTTP
    outboundHttpAclEntry = t.add_resource(
        NetworkAclEntry(
            'OutboundHTTPNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='100',
            Protocol=6,
            PortRange=PortRange(To='80', From='80'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Outbound ACL Rule for HTTPS
    outboundHttpsAclEntry = t.add_resource(
        NetworkAclEntry(
            'OutboundHTTPSNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='200',
            Protocol=6,
            PortRange=PortRange(To='443', From='443'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Outbound ACL Rule for SSH
    outboundSshAclEntry = t.add_resource(
        NetworkAclEntry(
            'OutboundSSHNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='300',
            Protocol=6,
            PortRange=PortRange(To='22', From='22'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Outbound ACL Rule for Ephemeral Response Ports
    outboundResponsePortsAclEntry = t.add_resource(
        NetworkAclEntry(
            'OutboundResponsePortsNetworkAclEntry',
            NetworkAclId=Ref(network_acl),
            RuleNumber='400',
            Protocol=6,
            PortRange=PortRange(To='65535', From='1024'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0'))

    # Associate our public Subnet with our new Network ACL
    subnet_network_acl_assoc = t.add_resource(
        SubnetNetworkAclAssociation(
            'SubnetNetworkAclAssociation',
            SubnetId=Ref(public_subnet),
            NetworkAclId=Ref(network_acl)))

    # Add a Security Group for our Web Server
    webserver_security_group = t.add_resource(
        SecurityGroup(
            'SecurityGroup',
            GroupDescription='Web Server SG',
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol='tcp',
                    ToPort='80',
                    FromPort='80',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    ToPort='22',
                    FromPort='22',
                    CidrIp='0.0.0.0/0')],
            VpcId=Ref(vpc)))

    # Add the Web Server Instance
    instance = t.add_resource(
        Instance(
            'WebServerInstance',
            ImageId=supported_regions_ami_map[region],
            InstanceType=type_instance,
            KeyName=key_pair,
            NetworkInterfaces=
            [
                NetworkInterfaceProperty(
                    GroupSet=[Ref(webserver_security_group)],
                    AssociatePublicIpAddress='true',
                    DeviceIndex='0',
                    DeleteOnTermination='true',
                    SubnetId=Ref(public_subnet))
            ],
            UserData=Base64(
                Join(
                    '\n',
                    [
                        '#!/bin/bash -x',
                        'yum install httpd -y',
                        'yum update -y',
                        'echo "<html><h1>Automation for the People</h1></html>" ' \
                        '> /var/www/html/index.html',
                        'service httpd start',
                        'chkconfig httpd on'
                    ])),
            Tags=Tags(
                Application=ref_stack_id,
                Name=NAME_PREFIX+'webserver',
                Project=PROJECT)))

    # Add Outputs to the Template for the VPC ID and URL
    t.add_output(
        [
            Output('VPC',
                   Description='VPC ID',
                   Value=Ref(vpc)
                  ),
            Output('URL',
                   Description='Web Server URL',
                   Value=Join('',
                       [
                           'http://',
                            GetAtt('WebServerInstance',
                                   'PublicIp')
                       ])
                  )
        ])

    return t


def create_stack(id, secret, key_pair, region, template):
    ''' Create the Cloud Formation Stack from the specified Template'''

    # Create boto3 client for AWS Cloud Formation
    client = boto3.client('cloudformation',
                          aws_access_key_id=id,
                          aws_secret_access_key=secret,
                          region_name=region)

    # Validate the CFT Syntax
    try:
        client.validate_template(TemplateBody=template.to_json())
        print 'Cloud Formation Template PASSED syntax validation'

        # Submit the Template for CF Stack creation
        try:
            client.create_stack(StackName=STACK_NAME,
                                TemplateBody=template.to_json())

            # Poll for CF Stack submission updates until a terminal state
            continue_polling = True
            while continue_polling:
                stack_events = client.describe_stack_events(StackName=STACK_NAME)
                stack_status = stack_events['StackEvents'][0]['ResourceStatus']
                if stack_status == 'ROLLBACK_COMPLETE':
                    print 'Cloud Formation Stack Submission Status : FAILED'
                    print 'Check the AWS Console for Stack "%s" for more details.' % STACK_NAME
                    continue_polling = False
                elif stack_status == 'CREATE_COMPLETE':
                    print 'Cloud Formation Stack Submission Status : COMPLETED'

                    # Poll for CF Stack build updates until a terminal state
                    while continue_polling:
                        stack_details = client.describe_stacks(StackName=STACK_NAME)
                        stack_build_status = stack_details['Stacks'][0]['StackStatus']
                        if stack_build_status == 'ROLLBACK_COMPLETE':
                            print 'Cloud Formation Stack Build Status : FAILED'
                            print 'Check the AWS Console for Stack "%s" for more details.' % STACK_NAME
                            continue_polling = False
                        elif stack_build_status == 'CREATE_COMPLETE':
                            print 'Cloud Formation Stack Build Status : COMPLETE'
                            
                            # Display useful information about the provisioned environment, including
                            #     the VPC ID and Web Server URL obtained from the Outputs of the CF Stack
                            stack_outputs = stack_details['Stacks'][0]['Outputs']
                            for stack_output in stack_outputs:
                                if stack_output['OutputKey'] == 'VPC':
                                    stack_vpc = stack_output['OutputValue']
                                else:
                                    stack_url = stack_output['OutputValue']
                            print '\nCloud Formation Stack Name: %s' % STACK_NAME
                            print 'AWS Region: %s' % region
                            print 'Key Pair: %s' % key_pair
                            print 'VPC ID: %s' % stack_vpc
                            print 'Web Server URL: %s\n' % stack_url
                            print '\nNOTE: It may take a few minutes for the Web Server to start, so' \
                                  '\n      periodically hit refresh in your browser until the page is displayed.\n'
                            continue_polling = False
                        else:
                            print 'Cloud Formation Stack Build Status : Building...'
                            time.sleep(10)
                else:
                    print 'Cloud Formation Stack Submission Status : Creating...'
                    time.sleep(10)

        except botocore.exceptions.ClientError, err:
            print 'Cloud Formation Stack creation FAILED: ' \
                  '%s' % err.response['Error']['Message']

    except botocore.exceptions.ClientError, err:
        print 'Cloud Formation Template FAILED syntax validation: ' \
              '%s' % err.response['Error']['Message']


def parse_args_and_run(args=None):
    """ Parse command line arguments and provision the environment """

    parser = argparse.ArgumentParser(
                          description='Provisions an AWS cloud environment with a web server.')

    parser.add_argument(
        '-i',
        '--id',
        required=True,
        help='AWS Access Key ID'
    )
    parser.add_argument(
        '-s',
        '--secret',
        required=True,
        help='AWS Secret Access Key'
    )
    parser.add_argument(
        '-k',
        '--key_pair',
        required=True,
        help='Name of AWS Key Pair to use for Web Server Instance to allow SSH login'
    )
    parser.add_argument(
        '-r',
        '--region',
        default='us-east-1',
        action=ValidateRegion,
        help='AWS Region ID'
    )
    parser.add_argument(
        '-t',
        '--type_instance',
        default='t2.micro',
        help='AWS Instance Type/Size (e.g., "t2.micro")'
    )

    _args = parser.parse_args(args)
    provision_environment(_args.id,
                          _args.secret,
                          _args.key_pair,
                          _args.region,
                          _args.type_instance)


class ValidateRegion(argparse.Action):
    """ Class to validate AWS Region argument """

    def __call__(self, parser, namespace, values, option_string=None):
        if values not in supported_regions_ami_map:
            print '\n"%s" is not a supported AWS Region. Select from the following:' % values
            for key in sorted(supported_regions_ami_map.keys()):
                print '  %s' % key
            print ''
            exit(0)
        setattr(namespace, self.dest, values)


if __name__ == '__main__':
    parse_args_and_run()


