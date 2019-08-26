# aws-python-tools

Repository containing Python tools for AWS

## Websync

Web-sync is a program that wil sync a local directory to an s3 bucket and can configure Route 53 DNS records and Cloudfront to create a secure static website hosted on specified s3 bucket.  

### Features

Web-sync has the following features:

- Adds/Removes tags from bucket.
- Create bucket and configure static website.
- Creates Route53 DNS Hosted Zone.and configures Alias record for static s3 website.
- Enables/Disables file versioning on bucket.
- List buckets.
- List bucket contents.
- Sets AWS Profile with --profile="ProfileName"
- Syncs directory and subdirectories to S3 bucket.

### Requirements

Web-sync requires the following:

- AWS User with permissions to create s3 Buckets, DNS Zones/Records, and Cloudfront.
- AWS CLI installed.
- AWS profile configured with credentials.  If you AWS CLI Installed you can configure profile with:
    $ aws configure --profile "profile-name"

### Installation

- cd aws-python-tools\websync
- pip install Websync-0.6-py3-none-any.whl

### Examples
- websync [Option] COMMAND [ARGS]
- websync setup-bucket "test.yourdomain.com"
- websync sync-bucket "folder" "yourbucket"
- websync setup-cloudfront "test.yourdomain.com" 

### TO-DO
- More secure bucket policy.
- Option to set Cloudfront to use only North America / NA + Europe / Worldwide servers.
- Create a better example website.
