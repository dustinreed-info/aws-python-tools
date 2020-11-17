# aws-python-tools

Repository containing Python tools for AWS

## Websync

Web-sync is a program that wil sync a local directory to an s3 bucket and can configure Route 53 DNS records and 
Cloudfront to create and distribute secure static website hosted on specified s3 bucket.  

### Features

Web-sync has the following features:

- Adds/Removes tags from s3 buckets and CloudFront Distributions.
- Create bucket and configure static website.
- Creates Route53 DNS Hosted Zone.and configures Alias record to point CloudFront or S3.
- Deploys CloudFront CDN to distribute website hosted in s3.
- Enables/Disables file versioning on bucket.
- List buckets.
- List bucket contents.
- Sets AWS Profile with --profile="ProfileName"
- Syncs directory and subdirectories to S3 bucket.
    Sync-bucket will remove files from bucket that do not exist locally.


### Requirements

Web-sync requires the following:

- AWS User with permissions to create s3 Buckets, DNS Zones/Records, and Cloudfront.
- AWS CLI installed.
- AWS profile configured with credentials.  If you AWS CLI Installed you can configure profile with:
    $ aws configure --profile "profile-name"
- S3 Bucket name must match domain name that you want to setup.  For example:
    BucketName: "test.websitetest.net"
    DomainName: "test.websitetest.net"
- SSL certificate for domain that you want to deploy CloudFront Distributino to.

### Installation
```
pip install pipenv
pipenv run sudo python3 ./setup.py install 
```

### Alternative Install
```
pip install ./dist/Websync-0.50-py3-none-any.whl
```
### Examples
- websync [Option] COMMAND [ARGS]
- websync --help
- websync setup-bucket "test.yourdomain.com"
- websync sync-bucket "folder" "yourbucket"
- websync setup-dns "test.yourdomain.com"
- websync setup-cloudfront "test.yourdomain.com" 

### TO-DO
- Option to set Cloudfront to use only North America / NA + Europe / Worldwide servers.
- Create a better example website.
