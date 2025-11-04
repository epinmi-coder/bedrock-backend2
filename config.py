
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional


def get_secret(parameter_name: str, region: str = "us-east-1") -> Optional[str]:
   
    try:
        # Initialize SSM client
        ssm = boto3.client("ssm", region_name=region)

        # Get parameter value
        response = ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True  # Decrypt if the parameter is a SecureString
        )

        return response["Parameter"]["Value"]

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        print(f"⚠️ Failed to get parameter '{parameter_name}': {error_code}")
        return None



