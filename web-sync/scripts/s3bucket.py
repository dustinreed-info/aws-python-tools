#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Classes to manage S3 Buckets."""

from pathlib import Path
import mimetypes
import boto3
from botocore.exceptions import ClientError


class BucketManager:
    """Manages an S3 Bucket."""
    def __init__(self, session):
        self.s3 = session.resource('s3')
        self.session = boto3.Session(profile_name='awstools')

    def all_buckets(self):
        """Gets an iterator for all s3 buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Gets an iterator for all objects in s3 bucket."""
        return self.s3.Bucket(bucket_name).objects.all()

    def create_bucket(self, bucket_name):
        """Creates s3 bucket."""
        self.new_bucket = None
        try:
            self.new_bucket = self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.session.region_name
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidLocationConstraint':
                self.new_bucket = self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.new_bucket = self.s3.Bucket(bucket_name)
        return self.new_bucket

    def suspend_bucket_versioning(self, bucket_name):
        """Suspends bucket versioning."""
        self.s3.Bucket(bucket_name).Versioning().delete()

    def list_bucket_tags(self, bucket_name):
        """Lists all tags for a specified bucket"""
        try:
            for t in self.s3.BucketTagging(bucket_name=bucket_name).tag_set:
                print(f"{t['Key']}: {t['Value']}")
        except:
            print(f'{bucket_name} does not have any tags set.')

    def remove_bucket_tag(self, bucket_name, key, value):
        """ Removes tag from specified s3 bucket"""
        new_tags = []
        try:
            tag = self.s3.BucketTagging(bucket_name=bucket_name).tag_set
            for t in tag:
                if key in t['Key']:
                    pass
                else:
                    new_tags.append(t)
            self.s3.BucketTagging(bucket_name=bucket_name).put(Tagging={
                'TagSet': new_tags
                }
            )
        except:
            print(f'{bucket_name} does not appear to have a {key} tag set.')

    def set_bucket_policy(self, bucket_name):
        """Sets bucket policy for *.html to be public."""
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
            """ % self.s3.Bucket(bucket_name).name
        policy = policy.strip()
        pol = self.s3.Bucket(bucket_name).Policy()
        pol.put(Policy=policy)

    def set_bucket_versioning(self, bucket_name):
        """Enables multiple versions of an object in the same bucket."""
        self.s3.Bucket(bucket_name).Versioning().enable()

    def set_bucket_website(self, bucket_name):
        """Configures a static website from s3 bucket.
        Index.html
        Error.html"""
        website = self.s3.Bucket(bucket_name).Website()
        website.put(WebsiteConfiguration={
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'}
            }
        )

    def set_bucket_tag(self, bucket_name, key='Creator', value='Web-Sync'):
        """Tags specified s3 bucket"""
        new_tags = []
        try:
            tag = self.s3.BucketTagging(bucket_name=bucket_name).tag_set
            for t in tag:
                if t['Key'] == key and t['Value'] == value:
                    pass
                elif key == t['Key']:
                    print(f'Tag was {key}: {t["Value"]} \nTag updated to {key}: {value}')
                else:
                    new_tags.append(t)
            new_tags.append({'Key': key, 'Value': value})
        except:
            print(f'Setting bucket tag to {key}: {value}')
            new_tags.append({'Key': key, 'Value': value})
        self.s3.BucketTagging(bucket_name=bucket_name).put(Tagging={
            'TagSet': new_tags
            }
        )

    def file_upload(self, bucket_name, path, key):
        self.s3.Bucket(bucket_name).upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': mimetypes.guess_type(key)[0] or 'text/plain'
            }
        )

    def sync_bucket(self, pathname, bucket):
        """Sync contents of pathname to s3 bucket."""
        root = Path(pathname).expanduser().resolve()
        s3_bucket = self.s3.Bucket(bucket)

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
                    self.file_upload(
                        s3_bucket.name,
                        str(each),
                        str(each.relative_to(root).as_posix())
                    )
        handle_dir(root)


# session = boto3.Session(profile_name='awstools')
# a = BucketManager(session)
# # a.remove_bucket_tag('aws-python-tools45645645', 'test5','1')
# a.tag_bucket('aws-python-tools45645645', 'test5','2')
# a.list_bucket_tags('aws-python-tools45645645')
