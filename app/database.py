import os
import boto3
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class DynamoDBClient:
    def __init__(self):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "ap-south-1")
        
        if not self.aws_access_key or not self.aws_secret_key:
            raise ValueError("AWS credentials not found in environment variables")
        
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )
        
        self.client = boto3.client(
            'dynamodb',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )
        
        logger.info(f"DynamoDB client initialized for region: {self.aws_region}")
    
    def get_table(self, table_name: str):
        return self.dynamodb.Table(table_name)

db_client = DynamoDBClient()

