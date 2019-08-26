from setuptools import setup

setup(
    name='Websync',
    version='0.6',
    author='Dustin Reed',
    author_email='dustin@dustinreed.info',
    description='Web-sync is a tool to deploy static websites to an s3 bucket and use CloudFront CDN to deliver it world wide.',
    license='GPLv3+',
    packages=['websync'],
    url='https://github.com/dustinreed-info/aws-python-tools',
    install_requires=[
        'boto3',
        'click'
    ],
    entry_points='''
        [console_scripts]
        websync=websync.websync:cli
    '''


)