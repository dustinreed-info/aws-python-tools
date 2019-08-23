#!/usr/bin/python
# -*- coding: utf-8 -*-

import boto3
from s3bucket import BucketManager


class SessionConfig:
    """Creates SessionConfig object"""
    def __init__(self, profile):
        self.session_cfg = {}
        if profile:
            self.session_cfg['profile_name'] = profile
        self.session = boto3.Session(**self.session_cfg)
