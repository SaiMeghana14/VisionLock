import boto3
import os

# AWS environment variables
REKOGNITION_COLLECTION = os.getenv("REKOGNITION_COLLECTION", "visionlock-collection")
BUCKET = os.getenv("S3_BUCKET", "visionlock-uploads")
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "VisionLockUsers")
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT", "visionlock-anomaly-endpoint")
IOT_TOPIC = os.getenv("IOT_TOPIC", "visionlock/doors/door001/control")
ALERT_TOPIC_ARN = os.getenv("ALERT_TOPIC_ARN", "")

# AWS clients
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
iot = boto3.client('iot-data')
sns = boto3.client('sns')
sagemaker = boto3.client('sagemaker-runtime')
