import json
import os
import uuid
import base64
import boto3
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE', 'Photos')
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')

# Initialize DynamoDB table
photos_table = dynamodb.Table(PHOTOS_TABLE)

def lambda_handler(event, context):
    """
    Lambda function to handle photo uploads.
    
    This function:
    1. Receives photo data and metadata from API Gateway
    2. Uploads the photo to S3
    3. Stores metadata in DynamoDB
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with photo ID and status
    """
    try:
        logger.info("Processing upload request")
        
        # Parse request body
        if 'body' not in event:
            return build_response(400, {"error": "Missing request body"})
            
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        # Validate request
        if 'photo' not in body or 'fileName' not in body:
            return build_response(400, {"error": "Missing required fields: photo and fileName"})
            
        # Extract data
        photo_data = body['photo']
        file_name = body['fileName']
        
        # Generate unique photo ID
        photo_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Decode base64 photo data
        try:
            # Check if the string starts with data:image prefix and extract the base64 part
            if photo_data.startswith('data:image'):
                photo_data = photo_data.split(',')[1]
            
            image_data = base64.b64decode(photo_data)
        except Exception as e:
            logger.error(f"Error decoding image: {str(e)}")
            return build_response(400, {"error": "Invalid image data"})
        
        # Generate S3 key
        file_extension = os.path.splitext(file_name)[1]
        s3_key = f"{photo_id}{file_extension}"
        
        # Upload to S3
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=image_data,
                ContentType=f"image/{file_extension[1:]}"  # Remove the dot from extension
            )
            logger.info(f"Photo uploaded to S3: {s3_key}")
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return build_response(500, {"error": "Failed to upload photo to storage"})
        
        # Save metadata to DynamoDB
        try:
            photos_table.put_item(
                Item={
                    'photoId': photo_id,
                    'fileName': file_name,
                    'uploadTimestamp': timestamp,
                    's3Key': s3_key
                }
            )
            logger.info(f"Metadata saved to DynamoDB for photo: {photo_id}")
        except Exception as e:
            logger.error(f"Error saving to DynamoDB: {str(e)}")
            # If DynamoDB fails, try to delete the S3 object to maintain consistency
            try:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
            except Exception:
                pass
            return build_response(500, {"error": "Failed to save photo metadata"})
        
        # Return success response
        return build_response(201, {
            "photoId": photo_id,
            "message": "Photo uploaded successfully"
        })
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return build_response(500, {"error": "Internal server error"})

def build_response(status_code, body):
    """
    Build a standardized API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        Formatted API Gateway response
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }