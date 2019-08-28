#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Classes to manage S3 Buckets."""

from pathlib import Path
import mimetypes
import boto3
import src.websync.utils
from functools import reduce
from hashlib import md5
from botocore.exceptions import ClientError


class BucketManager:
    """Methods to manage S3 buckets."""

    CHUNK_SIZE = 8388608

    def __init__(self, session):
        self.session = session
        self.s3 = self.session.resource('s3')
        # self.session = boto3.Session(profile_name='awstools')

        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNK_SIZE,
            multipart_threshold=self.CHUNK_SIZE
        )
        self.manifest = {}
        self.local_files = []

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

    def file_upload(self, bucket_name, path, key):
        """Uploads file to s3 bucket at key."""
        etag = self.get_file_etag(path)
        if self.manifest.get(key, '') == etag:
            print('Skipping', key, 'already exists in', bucket_name)
            return
        print(f'Uploading {key} to {bucket_name} bucket.')
        self.s3.Bucket(bucket_name).upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': mimetypes.guess_type(key)[0] or 'text/plain'
            },
            Config=self.transfer_config
        )

    def get_bucket_name(self, bucket):
        """Returns the buckets name"""
        return self.s3.Bucket(bucket).name

    def get_bucket_region(self, bucket):
        """Returns the bucket's region name."""
        return self.s3.meta.client.get_bucket_location(
            Bucket=bucket)['LocationConstraint'] or 'us-east-1'

    def get_bucket_tags(self, bucket_name):
        """Lists all tags for a specified bucket."""
        try:
            for t in self.s3.BucketTagging(bucket_name=bucket_name).tag_set:
                print(f"{t['Key']}: {t['Value']}")
        except:
            print(f'{bucket_name} does not have any tags set.')

    def get_bucket_url(self, bucket):
        """Returns url for s3 website endpoint"""
        return 'http://{}.{}'.format(
            bucket, utils.get_site(self.get_bucket_region(bucket)))

    @staticmethod
    def get_data_hash(data):
        """Generate md5 hash for data"""
        hash = md5()
        hash.update(data)
        return hash

    def get_file_etag(self, filepath):
        """Gets etag for a file."""
        hashes = []
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(self.CHUNK_SIZE)
                if not data:
                    break

                hashes.append(self.get_data_hash(data))
        if not hashes:
            return
        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            hash = self.get_data_hash(
                reduce(lambda x, y: x + y, (h.digest() for h in hashes))
                )

            return '"{}-{}"'.format(hash.hexdigest(), len(hashes))

    def remove_bucket_tag(self, bucket_name, key, value):
        """Removes tag from specified s3 bucket."""
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
                        "Resource": [
                            "arn:aws:s3:::%s/*.html",
                            "arn:aws:s3:::%s/imgs/*",
                            "arn:aws:s3:::%s/icons/*",
                            "arn:aws:s3:::%s/css/*.css",
                            "arn:aws:s3:::%s/public/*"
                        ]

                    }
                ]
            }
            """   # % self.s3.Bucket(bucket_name).name
        policy = policy.replace('%s', self.s3.Bucket(bucket_name).name).strip()
        pol = self.s3.Bucket(bucket_name).Policy()
        pol.put(Policy=policy)

    def set_cloud_front_bucket_policy(self, bucket_name, origin_access_id):
        """Sets bucket policy for *.html to be public."""
        oai_arn = f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity {origin_access_id}"
        policy = """
            {
                "Version": "2012-10-17",
                "Id": "Policy1566251860285",
                "Statement": [
                    {
                        "Sid": "Stmt1566251838784",
                        "Effect": "Allow",
                        "Principal": {"AWS": "%(arn)s"},
                        "Action": "s3:GetObject",
                        "Resource": [
                            "arn:aws:s3:::%(name)s/*.html",
                            "arn:aws:s3:::%(name)s/imgs/*",
                            "arn:aws:s3:::%(name)s/icons/*",
                            "arn:aws:s3:::%(name)s/css/*.css",
                            "arn:aws:s3:::%(name)s/public/*"
                        ]

                    }
                ]
            }
            """ % {'name': self.s3.Bucket(bucket_name).name, 'arn': oai_arn}
        policy = policy.strip()
        pol = self.s3.Bucket(bucket_name).Policy()
        pol.put(Policy=policy)

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

    def set_bucket_manifest(self, bucket):
        """Loads manifest for caching purposes."""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag']

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

    def suspend_bucket_versioning(self, bucket_name):
        """Suspends bucket versioning."""
        self.s3.Bucket(bucket_name).Versioning().delete()

    def sync_bucket(self, pathname, bucket):
        """Sync contents of pathname to s3 bucket."""
        root = Path(pathname).expanduser().resolve()
        s3_bucket = self.s3.Bucket(bucket)
        self.set_bucket_manifest(bucket)

        def handle_dir(pathname):
            """ Uploads directory and sub directories to s3 bucket."""
            path = Path(pathname)
            for each in path.iterdir():
                if each.is_dir():
                    handle_dir(each)
                else:
                    self.local_files.append(str(each.relative_to(root).as_posix()))
                    self.file_upload(
                        s3_bucket.name,
                        str(each),
                        str(each.relative_to(root).as_posix())
                    )
        handle_dir(root)
        del_list = []

        for file in self.local_files:
            try:
                del(self.manifest[file])
            except KeyError:
                # File does not exist in manifest.
                pass
        for k in self.manifest.keys():
            del_list.append(
                {'Key': k},
                )
        [print(f'Removing {file["Key"]} from {bucket}') for file in del_list]
        try:
            s3_bucket.delete_objects(
                Delete={
                    'Objects': del_list
                }
            )
        except:
            print('It does not appear that any files need to be removed.')
