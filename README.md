# aws-python-tools

Repository containing Python tools for AWS

## Websync

Web-sync is a program that wil sync a local directory to an s3 bucket and can configure Route 53 DNS records and Cloudfront to create a secure static website hosted on specified s3 bucket.

### Features

Websync has the following features:

- Adds/Removes tags from bucket.
- Create bucket and configure static website.
- Creates Route53 DNS Hosted Zone.and configures Alias record for static s3 website.
- Enables/Disables file versioning on bucket.
- List buckets.
- List bucket contents.
- Sets AWS Profile with --profile=<ProfileName>
- Syncs directory and subdirectories to S3 bucket.