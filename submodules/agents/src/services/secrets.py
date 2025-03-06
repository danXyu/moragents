# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
import json
from botocore.exceptions import ClientError
from models.config.config import Config
from functools import lru_cache
from logs import setup_logging

logger = setup_logging()

CONF = Config.get_instance()


@lru_cache(maxsize=128)
def get_secret(secret_name: str, region_name: str = "us-west-1") -> str:
    """Get a secret from AWS Secrets Manager"""

    # Check if secret exists in config first
    if CONF.has(secret_name, "integrations"):
        logger.info(f"Returning secret value for '{secret_name}' from config")
        return CONF.get(secret_name, "integrations")

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        logger.info(f"Attempting to retrieve secret '{secret_name}' from region '{region_name}'")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        logger.info(f"Successfully retrieved secret '{secret_name}'")
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.error(f"Failed to retrieve secret '{secret_name}': {str(e)}")
        raise e

    secret = get_secret_value_response["SecretString"]
    logger.info(f"Returning secret value for '{secret_name}'")

    # Parse the JSON string into a dictionary and get the value
    secret_dict = json.loads(secret)
    return secret_dict.get(secret_name)
