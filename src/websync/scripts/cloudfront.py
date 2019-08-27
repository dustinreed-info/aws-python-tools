#!/usr/bin/python
# -*- coding: utf-8 -*-

import uuid
import boto3
from session import SessionConfig
# from session import SessionConfig


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
                            'DomainName': '{}.s3.amazonaws.com'.format(domain_name),
                            'S3OriginConfig': {
                                'OriginAccessIdentity': 'origin-access-identity/cloudfront/{}'.format(origin_access_id)
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
        oai_id = self.client.create_cloud_front_origin_access_identity(CloudFrontOriginAccessIdentityConfig={
            'CallerReference': str(uuid.uuid4()),
            'Comment': domain_name
            }            
        )
        return oai_id['CloudFrontOriginAccessIdentity']['Id']
    
    def get_origin_access_identity(self, domain_name):
        oai_list = self.client.list_cloud_front_origin_access_identities()['CloudFrontOriginAccessIdentityList']['Items']
        paginator = self.client.get_paginator('list_cloud_front_origin_access_identities')
        for page in paginator.paginate():
            for item in oai_list:
                if domain_name == item['Comment']:
                    return self.client.get_cloud_front_origin_access_identity(Id=item['Id'])['CloudFrontOriginAccessIdentity']['Id']

    def get_origin_access_identity_config(self, domain_name):
        oai_list = self.client.list_cloud_front_origin_access_identities()['CloudFrontOriginAccessIdentityList']['Items']
        paginator = self.client.get_paginator('list_cloud_front_origin_access_identities')
        for page in paginator.paginate():
            for item in oai_list:
                if domain_name == item['Comment']:
                    return self.client.get_cloud_front_origin_access_identity_config(Id=item['Id'])

    def get_matching_distributions(self, domain_name):
        """List matching CloudFront distributions for a domain name."""
        paginator = self.client.get_paginator('list_distributions')
        for page in paginator.paginate():

            for item in page['DistributionList']['Items']:
                aliases = str(item['Aliases']['Items'])
                if domain_name in aliases:
                    return item
        return None

    def remove_cloud_front_tag(self, domain_name, tag_key='Creator'):
        """Removes tag from specified Cloud Front Distribution."""

        cf_arn = self.get_matching_distributions(domain_name)['ARN']

        if cf_arn:        
            self.client.untag_resource(
                Resource=cf_arn,
                TagKeys={
                    'Items': [
                        tag_key,
                    ]
                }
            )
            return print(f'Removing {tag_key} from {cf_arn}.')
        return print(f'CloudFront Distribution ARN: {cf_arn}, does not appear to exist.')
                

    def set_cloud_front_tag(self, domain_name, key='Creator', value='Web-Sync'):
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



session = SessionConfig('awstools').session
domain_name = 'websync.dustinreed.info'
cf = CloudFrontManager(session)
pass
# cf.create_origin_access_identity('box4.dustinreed.info')

# oai_list = client.list_cloud_front_origin_access_identities()['CloudFrontOriginAccessIdentityList']['Items']

# for item in oai_list:
#     if domain_name == item['Comment']:
#         return item['Id']
# print('No OAI ID matching {domain_name} found.  Creating new OAI ID.')
    # self.create_origin_access_identity(self, domain_name)        ##Create method