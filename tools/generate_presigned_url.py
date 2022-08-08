'''Script to generate presigned url for an object in S3.

USAGE:
    python generate_presigned_url.py <s3 url for the object> <expiration time in seconds>

Example:
    python generate_presigned_url.py s3://docs.canvara.com/api.html 7776000
'''

import argparse
import urllib.parse

import boto3


def generate_presigned_url(uri, expiration):
    parsed_uri = urllib.parse.urlparse(uri)

    return boto3.client('s3').generate_presigned_url(
        'get_object',
        Params={
            'Bucket': parsed_uri.netloc,
            'Key': parsed_uri.path.lstrip('/')
        },
        ExpiresIn=int(expiration)
    )


def main():
    parser = argparse.ArgumentParser(description='Generate a pre-signed url.')
    parser.add_argument('uri', help='S3 uri of the object')
    parser.add_argument('expiration', help='Expiration time in seconds')
    args = parser.parse_args()

    print(generate_presigned_url(args.uri, args.expiration))


if __name__ == '__main__':
    main()
