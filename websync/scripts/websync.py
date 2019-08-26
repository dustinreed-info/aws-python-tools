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
import click
import boto3
from botocore.exceptions import ClientError
from scripts.dns import DNS_Manager
from scripts.cert import CertificateManager
from scripts.cloudfront import CloudFrontManager
from scripts.s3bucket import BucketManager
from scripts.session import SessionConfig
from scripts import utils

bucket_manager = None
dns_manager = None
certificate_manager = None
cloudfront_manager = None


@click.group()
@click.option('--profile', default=None, help='Selects an AWS profile.')
def cli(profile):
    """Web Sync deploys websites to AWS."""
    global bucket_manager, dns_manager, certificate_manager, cloudfront_manager
    boto_session = SessionConfig(profile).session
    bucket_manager = BucketManager(boto_session)
    dns_manager = DNS_Manager(boto_session)
    certificate_manager = CertificateManager(boto_session)
    cloudfront_manager = CloudFrontManager(boto_session)


@cli.command('disable-bucket-versions')
@click.argument('bucket')
def disable_bucket_versioning(bucket):
    """Disables multiple versions of an object in the same bucket."""
    bucket_manager.suspend_bucket_versioning(bucket)


@cli.command('enable-bucket-versions')
@click.argument('bucket')
def enable_bucket_versioning(bucket):
    """Keep multiple versions of an object in the same bucket."""
    bucket_manager.set_bucket_versioning(bucket)


@cli.command('find-cert')
@click.argument('domain')
def find_certificate(domain):
    """Returns matching certificate for a domain."""
    print(certificate_manager.get_matching_certificates((domain)))


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an s3 bucket."""
    for obj in bucket_manager.all_objects(bucket):
        print(obj.key)


@cli.command('list-bucket-tags')
@click.argument('bucket')
def list_bucket_tags(bucket):
    """Lists tags for specified s3 bucket."""
    bucket_manager.list_bucket_tags(bucket)


@cli.command('list-buckets')
def list_buckets():
    """Lists all S3 Buckets."""
    for b in bucket_manager.all_buckets():
        print(b.name)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Creates and configures an s3 bucket."""
    bucket_manager.create_bucket(bucket)
    bucket_manager.set_bucket_versioning(bucket)
    bucket_manager.set_bucket_tag(bucket)
    bucket_manager.set_bucket_policy(bucket)
    bucket_manager.set_bucket_website(bucket)


@cli.command('setup-cloudfront')
@click.argument('domain')
@click.argument('bucket')
def setup_cloudfront(domain, bucket):
    """Setups CloudFront."""
    cf_dist = cloudfront_manager.get_matching_distributions(domain)
    print(cf_dist)
    if not cf_dist:
        certificate = certificate_manager.get_matching_certificates(domain)
        if not certificate:
            print('No matching certificate found.  Existing Application')
            return False
        cf_dist = cloudfront_manager.create_distribution(domain, certificate)
        print('Waiting for distribution deployment...')
        cloudfront_manager.awaiting_deployment(cf_dist)

    zone = dns_manager.get_hosted_zone(domain) \
        or dns_manager.create_hosted_zone(domain)
    dns_manager.create_cf_dns_record(
        zone,
        domain,
        cf_dist['DomainName']
    )
    print(f"Domain configured: https://{domain}")


@cli.command('setup-dns')
@click.argument('domain')
def setup_dns(domain):
    """Creates DNS Alias Record to point to static s3 bucket hosting website"""
    bucket = bucket_manager.get_bucket_name(domain)
    zone = dns_manager.get_hosted_zone(domain) \
        or dns_manager.create_hosted_zone(domain)
    endpoint = utils.get_endpoint(bucket_manager.get_bucket_region(bucket))
    a_record = dns_manager.create_s3_dns_record(
        zone,
        domain,
        endpoint)
    print(f"Domain configured: http://{domain}")


@cli.command('sync-bucket')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Syncs directory and subdirectories to specified s3 bucket"""
    bucket_manager.sync_bucket(pathname, bucket)
    print('Static website URL: ', bucket_manager.get_bucket_url(bucket))


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


if __name__ == '__main__':
    cli()
