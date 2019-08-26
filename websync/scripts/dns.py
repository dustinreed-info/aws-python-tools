#!/usr/bin/python
# -*- coding: utf-8 -*-

import uuid
from scripts import utils

"""Classes for AWS Route 53 DNS."""


class DNS_Manager:
    """Methods to manage Route53 DNS."""
    def __init__(self, session):
        self.client = session.client('route53')
        self.session = session

    def create_cf_dns_record(self, zone, domain_name, cf_dist):
        """Creates DNS record for CloudFront Distribution."""
        return self.client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Created by web-sync',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain_name,
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': 'Z2FDTNDATAQYW2',
                                'DNSName': cf_dist,
                                'EvaluateTargetHealth': False
                            }
                        }
                    }
                ]
            }
        )

    def create_hosted_zone(self, domain_name):
        """Creates a hosted zone in Route53 DNS"""
        zone_name = ".".join(domain_name.split('.')[-2:]) + "."
        return self.client.create_hosted_zone(
            Name=zone_name,
            CallerReference=str(uuid.uuid4())
        )

    def create_s3_dns_record(self, zone, domain_name, endpoint):
        """Creates DNS record for static website hosted in S3 Bucket."""
        return self.client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Created by web-sync',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain_name,
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': endpoint.dnszone,
                                'DNSName': endpoint.site,
                                'EvaluateTargetHealth': False
                            }
                        }
                    }
                ]
            }
        )

    def get_hosted_zone(self, domain_name):
        paginator = self.client.get_paginator('list_hosted_zones')
        for page in paginator.paginate():
            for zone in page['HostedZones']:
                if domain_name.endswith(zone['Name'][:-1]):
                    return zone
            return None
