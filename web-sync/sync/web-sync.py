#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Web-Sync: automates the process of deploying static websites to S3.

- Configures AWS S3 Buckets
    - Creates bucket
    - Sets bucket up for static website hosting
    - Syncs local files to s3 Bucket
- Configures DNS with AWS Route 53
- Configures AWS CloudFront CDN
"""

from pathlib import Path
import mimetypes
import click
import boto3
from botocore.exceptions import ClientError

# Selects profile from ~/.aws/config
session = boto3.Session(profile_name='awstools')
s3 = session.resource('s3')


@click.group()
def cli():
    """Web Sync deploys websites to AWS."""
    pass


@cli.command('list-buckets')
def list_buckets():
    """Lists all S3 Buckets."""
    for b in s3.buckets.all():
        print(b.name)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an s3 bucket."""
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


@cli.command('enable-versions')
@click.argument('bucket')
def enable_bucket_versioning(bucket):
    """Keep multiple versions of an object in the same bucket."""
    bucket = s3.Bucket(bucket)
    bucket.Versioning().enable()


@cli.command('disable-versions')
@click.argument('bucket')
def disable_bucket_versioning(bucket):
    """Disables multiple versions of an object in the same bucket."""
    bucket = s3.Bucket(bucket)
    bucket.Versioning().suspend()


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Creates and configures an s3 bucket."""
    new_bucket = None
    try:
        new_bucket = s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={
                'LocationConstraint': session.region_name
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidLocationConstraint':
            new_bucket = s3.create_bucket(Bucket=bucket)
        else:
            new_bucket = s3.Bucket(bucket)

    new_bucket.Versioning().enable()
    s3.BucketTagging(bucket_name=bucket).put(Tagging={
        'TagSet':
            [
                {
                    'Key': 'Creator',
                    'Value': 'web-sync'
                }
            ]
        }
    )

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
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
            },
        'IndexDocument': {
            'Suffix': 'index.html'
            }
        }
    )
    return


def file_upload(s3_bucket, path, key):
    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': mimetypes.guess_type(key)[0] or 'text/plain'
        }
    )


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def Sync(pathname, bucket):
    """Sync contents of pathname to s3 bucket."""
    root = Path(pathname).expanduser().resolve()
    s3_bucket = s3.Bucket(bucket)

    def handle_dir(pathname):
        """ Uploads directory and sub directories to s3 bucket."""
        path = Path(pathname)
        for each in path.iterdir():
            if each.is_dir():
                handle_dir(each)
            else:
                print("Uploading file {} to {} bucket.".format(
                    each.relative_to(root).as_posix(), s3_bucket.name
                    )
                )
                file_upload(
                    s3_bucket,
                    str(each),
                    str(each.relative_to(root).as_posix())
                )
    handle_dir(root)

if __name__ == '__main__':
    cli()
