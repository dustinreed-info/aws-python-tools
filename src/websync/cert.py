#!/usr/bin/python
# -*- coding: utf-8 -*-

import boto3

"""Classes to manage SSL Certificates."""


class CertificateManager:
    """Manage an ACM Certificate"""
    def __init__(self, session):
        self.session = session
        self.client = self.session.client('acm', region_name='us-east-1')

    def cert_matches(self, cert_arn, domain_name):
        """Returns True if certificate san matches exactly or is a * match"""
        cert_info = self.client.describe_certificate(CertificateArn=cert_arn)
        alt_names = cert_info['Certificate']['SubjectAlternativeNames']
        for name in alt_names:
            if name == domain_name:
                return True
            elif name[0] == '*' and domain_name.endswith(name[1:]):
                return True
        return False

    def get_matching_certificates(self, domain_name):
        """Lists matching certificates for domain in ACM."""
        paginator = self.client.get_paginator('list_certificates')
        for page in paginator.paginate(CertificateStatuses=['ISSUED']):
            for cert in page['CertificateSummaryList']:
                        if self.cert_matches(cert['CertificateArn'], domain_name):
                            return cert
        return None
