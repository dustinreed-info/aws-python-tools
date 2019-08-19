import boto3
import sys
import click
from botocore.exceptions import ClientError

#Selects profile from ~/.aws/config
session = boto3.Session(profile_name='awstools')
s3 = session.resource('s3')

@click.group()
def cli():
    "Web Sync deploys websites to AWS"
    pass

@cli.command('list-buckets')
def list_buckets():
    "Lists all S3 Buckets"
    for b in s3.buckets.all():
        print(b)

@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    "List objects in an s3 bucket"
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)

@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    "Creates and configures an s3 bucket"
    new_bucket = None
    try:
        new_bucket = s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={'LocationConstraint': session.region_name})
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidLocationConstraint':
            new_bucket = s3.create_bucket(Bucket=bucket)
        else:
            new_bucket = s3.Bucket(bucket)


    new_bucket.upload_file('index.html', 'index.html', ExtraArgs={'ContentType': 'text/html'})
    policy = """
        {
            "Version": "2012-10-17",
            "Id": "Policy1566251860285",
            "Statement": [
                {
                    "Sid": "Stmt1566251838784",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::%s/*.html"
                }
            ]
        }
        """ % new_bucket.name
    policy = policy.strip()
    pol = new_bucket.Policy()
    pol.put(Policy=policy)
    ws = new_bucket.Website()
    ws.put(WebsiteConfiguration=
        {
        'ErrorDocument': 
            {
            'Key': 'error.html'
            },
        'IndexDocument': 
            {
            'Suffix': 'index.html'
            }
        }
    )
    return 
    #url = "https://%s.s3-website.%s.amazonaws.com" % (bucket.name, session.region_name)
if __name__ =='__main__':
    cli()
