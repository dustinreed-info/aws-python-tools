#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Web-Sync: automates the process of deploying static websites to S3.

- Configures AWS S3 Buckets
    - Creates bucket
    - Enables/Suspends s3 bucket versioning
    - Sets bucket up for static website hosting
    - Syncs local files to s3 Bucket
    - Add/Remove tag to s3 bucket
- Configures DNS with AWS Route 53
- Configures AWS CloudFront CDN
"""

from pathlib import Path
import mimetypes
import click
import boto3
from botocore.exceptions import ClientError
from s3bucket import BucketManager


# Selects profile from ~/.aws/config
session = boto3.Session(profile_name='awstools')
# s3 = session.resource('s3')

bucket_manager = BucketManager(session)


@click.group()
def cli():
    """Web Sync deploys websites to AWS."""
    pass


@cli.command('list-buckets')
def list_buckets():
    """Lists all S3 Buckets."""
    for b in bucket_manager.all_buckets():
        print(b.name)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an s3 bucket."""
    for obj in bucket_manager.all_objects(bucket):
        print(obj.key)


@cli.command('enable-versions')
@click.argument('bucket')
def enable_bucket_versioning(bucket):
    """Keep multiple versions of an object in the same bucket."""
    # bucket = bucket_manager.s3.Bucket(bucket)
    # bucket.Versioning().enable()
    bucket_manager.set_bucket_versioning(bucket)


@cli.command('disable-versions')
@click.argument('bucket')
def disable_bucket_versioning(bucket):
    """Disables multiple versions of an object in the same bucket."""
    # bucket = bucket_manager.s3.Bucket(bucket)
    # bucket.Versioning().suspend()
    bucket_manager.suspend_bucket_versioning(bucket)

@cli.command('list-bucket-tags')
@click.argument('bucket')
def list_bucket_tags(bucket):
    """Lists tags for specified s3 bucket."""
    bucket_manager.list_bucket_tags(bucket)
@cli.command('tag-bucket')
@click.argument('bucket')
@click.argument('tagkey')
@click.argument('tagvalue')
def tag_bucket(bucket, tagkey, tagvalue):
    """Tags specified s3 bucket."""
    bucket_manager.set_bucket_tag(bucket, tagkey, tagvalue)

@cli.command('untag-bucket')
@click.argument('bucket')
@click.argument('tagkey')
@click.argument('tagvalue', required=False)
def untag_bucket(bucket, tagkey, tagvalue=None):
    """Removes tag from s3 bucket."""
    bucket_manager.remove_bucket_tag(bucket, tagkey, tagvalue)

@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Creates and configures an s3 bucket."""
    bucket_manager.create_bucket(bucket)
    bucket_manager.set_bucket_versioning(bucket)
    bucket_manager.set_bucket_tag(bucket)
    bucket_manager.set_bucket_policy(bucket)
    bucket_manager.set_bucket_website(bucket)


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
    s3_bucket = bucket_manager.s3.Bucket(bucket)

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
