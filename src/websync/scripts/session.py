#!/usr/bin/python
# -*- coding: utf-8 -*-

import boto3

class SessionConfig(object):
    """Creates a SessionConfig object
    test
    """
    def __init__(self, profile):
        self.session_cfg = {}
        if profile:
            self.session_cfg['profile_name'] = profile
        self.session = boto3.Session(**self.session_cfg)
