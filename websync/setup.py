from setuptools import setup

setup(
    name='Web-sync',
    version='0.1',
    author='Dustin Reed',
    author_email='dustin@dustinreed.info',
    description='Web-sync is a tool to deploy static websites to an s3 bucket and use CloudFront CDN to deliver it world wide.',
    packages=['web-sync'],
    url='https://github.com/dustinreed-info/aws-python-tools',
    install_requires=[
        'boto3',
        'click'
    ],
    entry_points='''
        [console_scripts]
        websync=scripts.websync:cli
    '''


)