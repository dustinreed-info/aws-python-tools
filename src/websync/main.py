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
from dns import DNS_Manager
from cert import CertificateManager
from cloudfront import CloudFrontManager
from s3bucket import BucketManager
from session import SessionConfig
import utils



class Manager(object):
    def __init__(self, boto_session):
        self.bucket_manager = BucketManager(boto_session) 
        self.dns_manager = DNS_Manager(boto_session)
        self.certificate_manager = CertificateManager(boto_session)
        self.cloudfront_manager = CloudFrontManager(boto_session)

@click.group()
@click.option('--profile', default=None, help='Selects an AWS profile.')
@click.pass_context
def cli(ctx, profile):
    """Web Sync deploys websites to AWS."""
    boto_session = SessionConfig(profile).session
    ctx.obj = Manager(boto_session)


@cli.command('disable-bucket-versions')
@click.argument('bucket')
@click.pass_obj
def disable_bucket_versioning(mgr, bucket):
    """Disables multiple versions of an object in the same bucket."""
    mgr.bucket_manager.suspend_bucket_versioning(bucket)


@cli.command('enable-bucket-versions')
@click.argument('bucket')
@click.pass_obj
def enable_bucket_versioning(mgr, bucket):
    """Keep multiple versions of an object in the same bucket."""
    mgr.bucket_manager.set_bucket_versioning(bucket)


@cli.command('find-cert')
@click.argument('domain')
@click.pass_obj
def find_certificate(mgr, domain):
    """Returns matching certificate for a domain."""
    print(mgr.certificate_manager.get_matching_certificates((domain)))


@cli.command('list-bucket-objects')
@click.argument('bucket')
@click.pass_obj
def list_bucket_objects(mgr, bucket):
    """List objects in an s3 bucket."""
    for obj in mgr.bucket_manager.all_objects(bucket):
        print(obj.key)


@cli.command('list-bucket-tags')
@click.argument('bucket')
@click.pass_obj
def list_bucket_tags(mgr, bucket):
    """Lists tags for specified s3 bucket."""
    mgr.bucket_manager.get_bucket_tags(bucket)


@cli.command('list-cloudfront-tags')
@click.argument('domain')
@click.pass_obj
def list_cloudfront_tags(mgr, domain):
    """Lists tags for CloudFront Distribution
    that matches specified domain."""
    mgr.cloudfront_manager.get_cloud_front_tags(domain)


@cli.command('list-buckets')
@click.pass_obj
def list_buckets(mgr):
    """Lists all S3 Buckets."""
    for b in mgr.bucket_manager.all_buckets():
        print(b.name)


@cli.command('setup-bucket')
@click.argument('bucket')
@click.pass_obj
def setup_bucket(mgr, bucket):
    """Creates and configures an s3 bucket."""
    mgr.bucket_manager.create_bucket(bucket)
    mgr.bucket_manager.set_bucket_versioning(bucket)
    mgr.bucket_manager.set_bucket_tag(bucket)
    mgr.bucket_manager.set_bucket_policy(bucket)
    mgr.bucket_manager.set_bucket_website(bucket)


@cli.command('setup-cloudfront')
@click.argument('domain')
@click.argument('bucket')
@click.pass_obj
def setup_cloudfront(mgr, domain, bucket):
    """Creates a  CloudFront Distribution.
        Checks for SSL Certificate matching domain.
        Checks for matching Origin Access ID and creates one if not found.
        Sets s3 bucket policy to use OA ID.
        Creates DNS A Alias record to point to CloudFront Distribution.
    """
    cf_dist = mgr.cloudfront_manager.get_matching_distributions(domain)
    print(cf_dist)
    if not cf_dist:
        certificate = mgr.certificate_manager.get_matching_certificates(domain)
        if not certificate:
            print('No matching certificate found.  Existing Application')
            return False
        cf_dist = mgr.cloudfront_manager.create_distribution_with_tags(domain, certificate)
        print('Waiting for distribution deployment...')
        print("It can take ~30 minutes for CloudFront to fully deploy the distribution ")
        mgr.cloudfront_manager.awaiting_deployment(cf_dist)

    print('Setting Bucket Policy for CloudFront Origin Access ID.')
    origin_access_id = mgr.cloudfront_manager.get_origin_access_identity(domain)
    mgr.bucket_manager.set_cloud_front_bucket_policy(bucket, origin_access_id)

    zone = mgr.dns_manager.get_hosted_zone(domain) \
        or mgr.dns_manager.create_hosted_zone(domain)
    mgr.dns_manager.create_cf_dns_record(
        zone,
        domain,
        cf_dist['DomainName']
    )
    print(f"Domain configured: https://{domain}")


@cli.command('setup-dns')
@click.argument('domain')
@click.pass_obj
def setup_dns(mgr, domain):
    """Creates DNS Alias Record to point to static s3 bucket hosting website"""
    bucket = mgr.bucket_manager.get_bucket_name(domain)
    zone = mgr.dns_manager.get_hosted_zone(domain) \
        or mgr.dns_manager.create_hosted_zone(domain)
    endpoint = utils.get_endpoint(mgr.bucket_manager.get_bucket_region(bucket))
    a_record = mgr.dns_manager.create_s3_dns_record(
        zone,
        domain,
        endpoint)
    print(f"Domain configured: http://{domain}")


@cli.command('sync-bucket')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
@click.pass_obj
def sync(mgr,pathname, bucket):
    """Syncs directory and subdirectories to specified s3 bucket"""
    mgr.bucket_manager.sync_bucket(pathname, bucket)
    print('Static website URL: ', mgr.bucket_manager.get_bucket_url(bucket))


@cli.command('tag-bucket')
@click.argument('bucket')
@click.argument('tagkey')
@click.argument('tagvalue')
@click.pass_obj
def tag_bucket(mgr, bucket, tagkey, tagvalue):
    """Tags specified s3 bucket."""
    mgr.bucket_manager.set_bucket_tag(bucket, tagkey, tagvalue)


@cli.command('tag-cloudfront')
@click.argument('domain')
@click.argument('tagkey')
@click.argument('tagvalue')
@click.pass_obj
def tag_cloud_front(mgr, domain, tagkey, tagvalue):
    """Adds tag to CloudFront distribution matching domain name specified."""
    mgr.cloudfront_manager.set_cloud_front_tag(domain, tagkey, tagvalue)


@cli.command('untag-cloudfront')
@click.argument('domain')
@click.argument('tagkey')
@click.argument('tagvalue', required=False)
@click.pass_obj
def tag_cloud_front(mgr, domain, tagkey, tagvalue=None):
    """Removes Tag from CloudFront distrbution matching domain name specified."""
    mgr.cloudfront_manager.remove_cloud_front_tag(domain, tagkey, tagvalue)


@cli.command('untag-bucket')
@click.argument('bucket')
@click.argument('tagkey')
@click.argument('tagvalue', required=False)
@click.pass_obj
def untag_bucket(mgr, bucket, tagkey, tagvalue=None):
    """Removes tag from s3 bucket."""
    mgr.bucket_manager.remove_bucket_tag(bucket, tagkey, tagvalue)


if __name__ == '__main__':
    cli()
