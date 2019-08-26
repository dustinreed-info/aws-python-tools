#!/usr/bin/python
# -*- coding: utf-8 -*-

import uuid
import boto3
from websync.session import SessionConfig


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

    def create_distribution(self, domain_name, certificate):
        origin_id = 'S3-' + domain_name
        result = self.client.create_distribution(
            DistributionConfig={
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
                            'DomainName': '{}.s3.amazonaws.com'.format(domain_name),
                            'S3OriginConfig': {
                                'OriginAccessIdentity': ''
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
                }
            }
        )
        return result['Distribution']

    def get_matching_distributions(self, domain_name):
        """List matching CloudFront distributions for a domain name."""
        paginator = self.client.get_paginator('list_distributions')
        for page in paginator.paginate():
            # pprint(page)
            for item in page['DistributionList']['Items']:
                aliases = str(item['Aliases']['Items'])
                if domain_name in aliases:
                    return item
        return None
