import boto3
import sys
import click

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


if __name__ =='__main__':
    cli()
