# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import json
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError
from logs import setup_logging
from models.config.config import Config

logger = setup_logging()

CONF = Config.get_instance()


@lru_cache(maxsize=128)
def get_secret(secret_name: str, region_name: str = "us-west-1") -> str:
    """Get a secret from AWS Secrets Manager"""

    # Check if secret exists in config first (for local development)
    if CONF.has(secret_name, "integrations"):
        logger.info(f"Returning secret value for '{secret_name}' from config")
        return CONF.get(secret_name, "integrations")

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        logger.info(
            f"Attempting to retrieve secret '{secret_name}' from region '{region_name}'"
        )
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        logger.info(f"Successfully retrieved secret '{secret_name}'")
    except ClientError as e:
        logger.error(f"Failed to retrieve secret '{secret_name}': {str(e)}")
        raise e

    # Get the secret string
    secret = get_secret_value_response["SecretString"]

    # Try to parse as JSON first (for secrets that contain multiple key-value pairs)
    try:
        secret_dict = json.loads(secret)
        # If the secret_name is a key in the dictionary, return its value
        if secret_name in secret_dict:
            return secret_dict.get(secret_name)
        # Otherwise return the entire dictionary or a specific value
        return secret_dict
    except json.JSONDecodeError:
        # If it's not JSON, return the raw string
        return secret
