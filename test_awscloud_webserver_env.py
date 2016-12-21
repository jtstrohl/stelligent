
# TODO: With more time, better infrastructure tests could be implemented with serverspec

import argparse
import urllib2
import boto3
import botocore


def test_environment(id, secret, address, region):
    """ Validates the provisioned web server cloud environment """

    # Validate infrastructure pieces
    validate_securitygroup(id, secret, region)
    validate_webserver(address)

    # If we haven't exited yet, we passed all tests
    print 'SUCCESS: All tests passed'

def validate_securitygroup(id, secret, region):
    """ Validates the Security Group exists with correct rules """

    # Create boto3 client for AWS EC2
    client = boto3.client('ec2',
                          aws_access_key_id=id,
                          aws_secret_access_key=secret,
                          region_name=region)

    # Describe the Security Group
    sgs = client.describe_security_groups(Filters=[{
                                                    'Name':'description',
                                                    'Values':['Web Server SG']
                                                   }])

    # Verify we found the Security Group
    if len(sgs['SecurityGroups']) == 0:
        print 'FAILURE: Could not find expected Security Group'
        exit(0)

    # Verify we had the appropriate Security Group Rules
    security_group = sgs['SecurityGroups'][0]
    security_group_id = security_group['GroupId']
    foundHttpRule = False
    foundSshRule = False
    for rule in security_group['IpPermissions']:
        if rule['FromPort'] == 80 and rule['ToPort'] == 80:
            foundHttpRule = True 
        if rule['FromPort'] == 22 and rule['ToPort'] == 22:
            foundSshRule = True
    if not (foundHttpRule and foundSshRule):
        print 'FAILURE: Could not find expected Security Group Rules'
        exit(0)

    # Describe the Web Server Instance
    instances = client.describe_instances(Filters=[{
                                                    'Name':'tag-value',
                                                    'Values':['jstrohl-miniproject-webserver']
                                                   },
                                                   {
                                                    'Name':'instance-state-name',
                                                    'Values':['running']
                                                   }])

    # Verify we found the Web Server Instance in "running" state
    if len(instances['Reservations']) == 0 or len(instances['Reservations'][0]['Instances']) == 0:
        print 'FAILURE: Could not find expected Web Server EC2 Instance'
        exit(0)

    # Verify that the Security Group is applied to the Web Server Instance
    instance = instances['Reservations'][0]['Instances'][0]
    foundSgId = False
    for sg in instance['SecurityGroups']:
        if sg['GroupId'] == security_group_id:
            foundSgId = True
    if not foundSgId:
        print 'FAILURE: Security Group was not associated with Web Server EC2 Instance'
        exit(0)


def validate_webserver(address):
    """ Validates the HTML content of the Web Server Page """

    response = urllib2.urlopen('http://' + address)
    html = response.read()
    if 'Automation for the People' not in html:
        print 'FAILURE: Webpage on Web Server Instance at http://%s did not contain '\
              'the text "Automation for the People"' % address
        exit(0)
       

def parse_args_and_run(args=None):
    """ Parse command line arguments and provision the environment """

    parser = argparse.ArgumentParser(
                          description='Validates an AWS cloud web server environment created '\
                                      'with the provision_awscloud_webserver_env.py script.')

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
        '-a',
        '--address',
        required=True,
        help='Public IP address of the Web Server Instance to test'
    )
    parser.add_argument(
        '-r',
        '--region',
        default='us-east-1',
        help='AWS Region ID'
    )

    _args = parser.parse_args(args)
    test_environment(_args.id,
                     _args.secret,
                     _args.address,
                     _args.region)


if __name__ == '__main__':
    parse_args_and_run()


