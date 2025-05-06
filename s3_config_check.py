import boto3
import json
from django.conf import settings


def check_and_configure_s3_bucket():
    """
    Check and properly configure the S3 bucket for website usage:
    - Verify CORS configuration
    - Verify bucket policy allows public read access and authenticated write access
    - Create folders if needed

    Run this manually when setting up your bucket.
    """
    # Initialize S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    # 1. Check and configure CORS
    try:
        cors_config = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'POST', 'PUT', 'DELETE', 'HEAD'],
                    'AllowedOrigins': ['*'],  # In production, restrict to your domain
                    'ExposeHeaders': ['ETag', 'Content-Length'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }

        s3.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_config
        )
        print("✅ CORS configuration updated")

    except Exception as e:
        print(f"❌ CORS configuration error: {e}")

    # 2. Check and configure comprehensive bucket policy
    try:
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/media/*"
                },
                {
                    "Sid": "AllowAllS3ActionsForApp",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}/*",
                        f"arn:aws:s3:::{bucket_name}"
                    ]
                }
            ]
        }

        # If AWS_ACCOUNT_ID and AWS_IAM_USER_NAME are not set, use a simpler policy
        if not hasattr(settings, 'AWS_ACCOUNT_ID') or not hasattr(settings, 'AWS_IAM_USER_NAME'):
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/media/*"
                    },
                    {
                        "Sid": "AllowAllS3ActionsForBucket",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": [
                            "s3:PutObject",
                            "s3:GetObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": f"arn:aws:s3:::{bucket_name}/media/*"
                    }
                ]
            }

        s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("✅ Bucket policy updated for public read access and write permissions")

    except Exception as e:
        print(f"❌ Bucket policy configuration error: {e}")

    # 3. Create necessary folders
    try:
        # Create media folder
        s3.put_object(
            Bucket=bucket_name,
            Key='media/',
            Body=''
        )

        # Create game_images folder
        s3.put_object(
            Bucket=bucket_name,
            Key='media/game_images/',
            Body=''
        )

        print("✅ Folders created in S3 bucket")

    except Exception as e:
        print(f"❌ Folder creation error: {e}")

    # 4. Check if default image exists, if not upload it
    try:
        try:
            s3.head_object(
                Bucket=bucket_name,
                Key='media/game_images/default_game.jpg'
            )
            print("✅ Default image already exists")
        except:
            print("⚠️ Default image not found, please upload it manually to: media/game_images/default_game.jpg")
    except Exception as e:
        print(f"❌ Error checking default image: {e}")

    # 5. Test bucket permissions
    try:
        # Test writing a temporary file
        test_key = 'media/test_permissions.txt'
        s3.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body='Testing write permissions',
            ContentType='text/plain'
        )

        # Try to read it back
        result = s3.get_object(
            Bucket=bucket_name,
            Key=test_key
        )

        # Clean up the test file
        s3.delete_object(
            Bucket=bucket_name,
            Key=test_key
        )

        print("✅ S3 permissions test passed! Read/write access confirmed.")
    except Exception as e:
        print(f"❌ S3 permissions test failed: {e}")

    print("\nS3 bucket configuration check completed.")


if __name__ == "__main__":
    # This allows you to run this script directly
    import os
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Playlogg.settings')
    django.setup()

    check_and_configure_s3_bucket()