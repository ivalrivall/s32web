from dotenv import load_dotenv, find_dotenv
import os
import boto3
from botocore.config import Config

load_dotenv(find_dotenv())

access_key = os.getenv("S3_ACCESS_KEY")
secret_key = os.getenv("S3_SECRET_KEY")
endpoint_url = os.getenv("S3_ENDPOINT_URL")
bucket_name = os.getenv("S3_BUCKET_NAME")

if not all([access_key, secret_key, endpoint_url]):
    raise Exception("Missing one or more required environment variables.")

config = Config(signature_version='s3v4')

s3 = boto3.client(
    's3',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    endpoint_url=endpoint_url,
    config=config,
    verify=True  # Enable SSL verification for security
)

def getItems(folder=""):
    folders = []
    files = []

    try:
        # First, try to list all objects in the bucket to see what's available
        try:
            list_response = s3.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in list_response:
                print(f"Found {len(list_response['Contents'])} objects in bucket")
                for obj in list_response['Contents'][:5]:  # Show first 5 objects
                    print(f"  - {obj.get('Key')}")
            else:
                print("Bucket appears to be empty")
        except Exception as e:
            print(f"Could not list bucket contents: {e}")

        # Ensure folder path ends with '/' for proper S3 prefix matching
        if folder and not folder.endswith('/'):
            folder = folder + '/'

        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket_name,
            Prefix=folder,
            Delimiter="/"
        )

        for page in page_iterator:
            # Subfolders (CommonPrefixes)
            for prefix in page.get('CommonPrefixes', []):
                folder_name = prefix.get('Prefix')
                if folder_name:
                    folders.append(folder_name)

            # Files (Contents)
            for obj in page.get('Contents', []):
                key = obj.get('Key')
                if key and key != folder:  # avoid listing the folder itself as a file
                    file_metadata = {
                        "Key": key,
                        "Size": obj.get("Size"),
                        "LastModified": obj.get("LastModified"),
                    }

                    # Try to get content type, but don't fail if we can't
                    try:
                        head_obj = s3.head_object(Bucket=bucket_name, Key=key)
                        file_metadata["ContentType"] = head_obj.get("ContentType")
                    except Exception as e:
                        # If we can't get head_object, just use a default content type
                        file_metadata["ContentType"] = "application/octet-stream"
                        print(f"Warning: Could not get content type for {key}: {e}")

                    files.append(file_metadata)

    except Exception as e:
        print(f"Error accessing S3 bucket: {e}")
        print(f"Bucket: {bucket_name}")
        print(f"Endpoint: {endpoint_url}")
        print(f"Access Key: {access_key[:10]}...")
        # Return empty results if S3 is not accessible
        return [], []

    return folders, files
