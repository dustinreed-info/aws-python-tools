import boto3
#Select profile from ~/.aws/config
session = boto3.Session(profile_name='awstools')
s3 = session.resource('s3')