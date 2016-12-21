=======================
stelligent mini-project
=======================


About
=====

This is Jonathan Strohl's Mini-Project for Stelligent.  This project is written in Python and provisions an AWS cloud environment for a simple web server using a single command.


Prerequisites
=============

- In order to use this tool, you must have an Amazon Web Services (AWS) account, along with the active API credentials (i.e., AWS Access Key ID and AWS Secret Access Key) for an IAM user who has permissions to create and configure VPCs, Internet Gateways, Subnets, Network ACLs, Route Tables, Security Groups, and EC2 Instances -- preferably AdministratorAccess.
- You must also have a valid AWS Key Pair created in the desired region where you wish to provision the web server environment.


Installation
============

- Make sure that you have Python 2.7 and "pip" installed.
- You will also need to install the Python library "troposphere" which is used to generate Cloud Formation Templates.

  - To install "troposhere", run the following command::

    $ sudo pip install trophosphere --upgrade

- Additionally, you will need to install the Python libraries "boto3" and "botocore" for connecting to AWS.

  - To install "boto3" and "botocore", run the following commands::

    $ sudo pip install boto3 --upgrade
    $ sudo pip install botocore --upgrade

- Download the Python (\*.py) scripts from this project to your local machine


Command Line Arguments
======================

- To see script usage, run the following command::

  $ python provision_awscloud_webserver_env.py --help

- Arguments include::

+-----------+------------+---------------------------------------------------------------------------------------+
| Argument  | Mandatory? | Value Description                                                                     |
+===========+============+=======================================================================================+
| -i        | Yes        | AWS Access Key ID                                                                     |
+-----------+------------+---------------------------------------------------------------------------------------+
| -s        | Yes        | AWS Secret Access Key                                                                 |
+-----------+------------+---------------------------------------------------------------------------------------+
| -k        | Yes        | Name of AWS Key Pair to use for Web Server Instance to allow SSH login                |
+-----------+------------+---------------------------------------------------------------------------------------+
| -r        | No         | AWS Region ID (default value is "us-east-1"; Only US regions are currently supported) |
+-----------+------------+---------------------------------------------------------------------------------------+
| -t        | No         | AWS Instance Type/Size (default value is "t2.micro" to target free-tier)              |
+-----------+------------+---------------------------------------------------------------------------------------+


Examples
========

A few simple examples of how to use the script to provision an AWS cloud environment for a simple web server would look like this::

  $ python provision_awscloud_webserver_env.py -i AKIAILPCYUO5IEZHQ7KT -s WsziZR5guQM156iCYvyGqPMR1U4wWicQwaOCSU7B -k mykeypair

  $ python provision_awscloud_webserver_env.py -i AKIAILPCYUO5IEZHQ7KT -s WsziZR5guQM156iCYvyGqPMR1U4wWicQwaOCSU7B -k mykeypair -r us-west-2

  $ python provision_awscloud_webserver_env.py -i AKIAILPCYUO5IEZHQ7KT -s WsziZR5guQM156iCYvyGqPMR1U4wWicQwaOCSU7B -k mykeypair -r us-east-1 -t m3.large


Output
======

- The "provision_awscloud_webserver_env.py" script will display the on-going progress of the submission and building of the Cloud Formation Stack.
- When the Stack is complete, the script will display:

  - The Cloud Formation Stack name
  - The AWS Region ID where the environment was provisioned
  - The AWS Key Pair that was used for the Web Server EC2 Instance
  - The VPC ID where the environemnt was provisioned
  - The URL (containing Public IP) that can be used to access the Web Server using a web browser once the Web Server has started


Testing
=======

The "test_awscloud_webserver_env.py" script can be used to verify that the Web Server EC2 Instance is running, has the correct Security Group and Security Group Rules applied, and that the web page contains the expected content (e.g., "Automation for the People").


Command Line Arguments for the Test Script
******************************************

- To see test script usage, run the following command::

  $ python test_awscloud_webserver_env.py --help

- Test script arguments include::

+-----------+------------+---------------------------------------------------------------------------------------+
| Argument  | Mandatory? | Value Description                                                                     |
+===========+============+=======================================================================================+
| -i        | Yes        | AWS Access Key ID                                                                     |
+-----------+------------+---------------------------------------------------------------------------------------+
| -s        | Yes        | AWS Secret Access Key                                                                 |
+-----------+------------+---------------------------------------------------------------------------------------+
| -a        | Yes        | Public IP Address for Web Server Instance (Output from provisioning script)           |
+-----------+------------+---------------------------------------------------------------------------------------+
| -r        | No         | AWS Region ID (default value is "us-east-1"; Only US regions are currently supported) |
+-----------+------------+---------------------------------------------------------------------------------------+

