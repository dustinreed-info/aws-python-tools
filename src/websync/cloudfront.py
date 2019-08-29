#!/usr/bin/python
# -*- coding: utf-8 -*-

import uuid
import boto3



class CloudFrontManager:
    """Classes to manage CloudFront Distributions."""
    def __init__(self, session):
        self.session = session
        self.client = self.session.client('cloudfront')

    def awaiting_deployment(self, dist):
        """Waits for distribution to be deployed."""
        waiter = self.client.get_waiter('distribution_deployed')
        waiter.wait(Id=dist['Id'], WaiterConfig={
            'Delay': 30,
            'MaxAttempts': 75
        })

    def create_distribution(self, domain_name, certificate, tag_key='Creator', tag_value='Web-Sync'):
        """Creates Cloud Front CDN Distribution.
        First it checks if an Origin Access ID exists for a domain.
        If one is not found it goes ahead and creates one.
        Then it will create a CloudFront Distribution with tags
        It sets index.html as the default root object.  If this is called
        by websync.setup_cloudfront() it will set the bucket
        policy for the s3 bucket that matches the specified domain name
        so that CloudFront can distribute the necessary resources for the
        static website.
        """

        origin_id = 'S3-' + domain_name
        origin_access_id_config = self.get_origin_access_identity_config(domain_name)

        if origin_access_id_config:
            origin_access_id = self.get_origin_access_identity(domain_name)
            print(f'Origin Access ID: {origin_access_id}')
        else:
            origin_access_id = self.create_origin_access_identity(domain_name)
        result = self.client.create_distribution_with_tags(
            DistributionConfigWithTags={
                'CallerReference': str(uuid.uuid4()),
                'Aliases': {
                    'Quantity': 1,
                    'Items': [
                        domain_name
                    ]
                },
                'DefaultRootObject': 'index.html',
                'Comment': 'Created by web-sync.',
                'Enabled': True,
                'Origins': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'Id': origin_id,
                            'DomainName': '{}.s3.amazonaws.com'.format(
                                domain_name
                                ),
                            'S3OriginConfig': {
                                'OriginAccessIdentity': 'origin-access-identity/cloudfront/{}'.format(
                                    origin_access_id
                                    )
                            }
                        }
                    ]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': origin_id,
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'TrustedSigners': {
                        'Quantity': 0,
                        'Enabled': False
                    },
                    'ForwardedValues': {
                        'Cookies': {
                            'Forward': 'all'
                        },
                        'Headers': {
                            'Quantity': 0
                        },
                        'QueryString': False,
                        'QueryStringCacheKeys': {
                            'Quantity': 0
                        }
                    },
                    'DefaultTTL': 86400,
                    'MinTTL': 3600
                },
                'ViewerCertificate': {
                    'ACMCertificateArn': certificate['CertificateArn'],
                    'SSLSupportMethod': 'sni-only',
                    'MinimumProtocolVersion': 'TLSv1.1_2016'
                },
                'Tags': {
                    'Items': [
                        {
                            'Key': tag_key,
                            'Value': tag_value
                        }
                    ]
                }
            }
        )
        return result['Distribution']

    def create_origin_access_identity(self, domain_name):
        """Creates Origin Access ID."""
        oai_id = self.client.create_cloud_front_origin_access_identity(
            CloudFrontOriginAccessIdentityConfig={
                'CallerReference': str(uuid.uuid4()),
                'Comment': domain_name
                }
        )
        return oai_id['CloudFrontOriginAccessIdentity']['Id']

    def get_origin_access_identity(self, domain_name):
        """Returns Origin Access ID."""
        oai_list = self.client.list_cloud_front_origin_access_identities()['CloudFrontOriginAccessIdentityList']['Items']
        paginator = self.client.get_paginator('list_cloud_front_origin_access_identities')
        for page in paginator.paginate():
            for item in oai_list:
                if domain_name == item['Comment']:
                    return self.client.get_cloud_front_origin_access_identity(
                        Id=item['Id']
                        )['CloudFrontOriginAccessIdentity']['Id']

    def get_origin_access_identity_config(self, domain_name):
        """Returns Origin Access ID Config."""
        oai_list = self.client.list_cloud_front_origin_access_identities()['CloudFrontOriginAccessIdentityList']['Items']
        paginator = self.client.get_paginator('list_cloud_front_origin_access_identities')
        for page in paginator.paginate():
            for item in oai_list:
                if domain_name == item['Comment']:
                    return self.client.get_cloud_front_origin_access_identity_config(Id=item['Id'])

    def get_matching_distributions(self, domain_name):
        """List CloudFront distributions that matches specified domain name."""
        paginator = self.client.get_paginator('list_distributions')
        for page in paginator.paginate():

            for item in page['DistributionList']['Items']:
                aliases = str(item['Aliases']['Items'])
                if domain_name in aliases:
                    return item
        return None

    def get_cloud_front_arn(self, domain_name):
        return self.get_matching_distributions(domain_name)['ARN']

    def get_cloud_front_tags(self, domain_name):
        cf_arn = self.get_cloud_front_arn(domain_name)
        tags = self.client.list_tags_for_resource(Resource=cf_arn)['Tags']['Items']
        for t in tags:
            print(t)
        return tags

    def remove_cloud_front_tag(self, domain_name, tag_key='Creator', tag_value=None):
        """Removes tag from specified Cloud Front Distribution."""

        cf_arn = self.get_cloud_front_arn(domain_name)

        if cf_arn:
            self.client.untag_resource(
                Resource=cf_arn,
                TagKeys={
                    'Items': [
                        tag_key,
                    ]
                }
            )
            return print(f'Removing tag "{tag_key}" from {cf_arn} for "{domain_name}".')
        return print(f'CloudFront Distribution ARN: {cf_arn}, does not appear to exist.')

    def set_cloud_front_tag(self, domain_name, tag_key='Creator', tag_value='Web-Sync', arn=None):
        """Tags specified Cloud Front Distribution"""
        if arn is None:
            arn = self.get_cloud_front_arn(domain_name)
        return self.client.tag_resource(
            Resource=arn,
            Tags={
                'Items': [
                    {
                        'Key': tag_key,
                        'Value': tag_value
                    },
                ]
            }
        )
