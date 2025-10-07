#!/usr/bin/env python3
"""
Test script to diagnose S3 connection issues
"""
import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def test_s3_connection():
    """Test S3 connection and list available buckets"""

    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    bucket_name = os.getenv("S3_BUCKET_NAME")  # Use environment variable or default

    print("=== S3 Connection Test ===")
    print(f"Endpoint: {endpoint_url}")
    print(f"Bucket: {bucket_name}")
    print(f"Access Key: {access_key[:10]}..." if access_key else "No access key")

    if not all([access_key, secret_key, endpoint_url]):
        print("❌ Missing required environment variables")
        return False

    try:
        # Create S3 client
        config = Config(signature_version='s3v4')
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            config=config,
            verify=True  # Enable SSL verification for security
        )

        print("✅ S3 client created successfully")

        # List all buckets
        print("\n=== Available Buckets ===")
        try:
            response = s3.list_buckets()
            buckets = response.get('Buckets', [])

            if not buckets:
                print("❌ No buckets found in this S3 account")
                return False
            else:
                print(f"Found {len(buckets)} bucket(s):")
                for bucket in buckets:
                    print(f"  - {bucket['Name']}")

                # Check if our target bucket exists
                if bucket_name in [b['Name'] for b in buckets]:
                    print(f"✅ Target bucket '{bucket_name}' exists")

                    # Try to list contents of the bucket
                    print(f"\n=== Contents of bucket '{bucket_name}' ===")
                    try:
                        list_response = s3.list_objects_v2(Bucket=bucket_name)
                        if 'Contents' in list_response:
                            print(f"Found {len(list_response['Contents'])} objects:")
                            for obj in list_response['Contents'][:10]:  # Show first 10
                                print(f"  - {obj.get('Key')}")
                        else:
                            print("Bucket is empty")
                    except Exception as e:
                        print(f"❌ Could not list bucket contents: {e}")

                    return True
                else:
                    print(f"❌ Target bucket '{bucket_name}' not found in available buckets")
                    return False

        except Exception as e:
            print(f"❌ Could not list buckets: {e}")
            return False

    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

if __name__ == "__main__":
    test_s3_connection()
