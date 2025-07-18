import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from botocore.exceptions import ClientError

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/get_photo'))

# Import the Lambda function
import app

class TestGetPhotoFunction(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('app.s3_client')
    @patch('app.photos_table')
    def test_successful_get_photo(self, mock_table, mock_s3):
        """Test successful photo retrieval"""
        # Mock DynamoDB response
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id.jpg'
            }
        }
        
        # Mock S3 pre-signed URL
        mock_s3.generate_presigned_url.return_value = 'https://example.com/presigned-url'
        
        # Create a test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], 'test-photo-id')
        self.assertEqual(response_body['fileName'], 'test.jpg')
        self.assertEqual(response_body['uploadTimestamp'], '2023-01-01T12:00:00')
        self.assertEqual(response_body['downloadUrl'], 'https://example.com/presigned-url')
        
        # Verify DynamoDB and S3 were called correctly
        mock_table.get_item.assert_called_once_with(Key={'photoId': 'test-photo-id'})
        mock_s3.generate_presigned_url.assert_called_once()

    def test_missing_photo_id(self):
        """Test error handling for missing photo ID"""
        # Create a test event with missing photo ID
        event = {
            'pathParameters': {}  # Missing photoId
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing photo ID')
        
        # Test with no pathParameters at all
        event = {}
        response = app.lambda_handler(event, {})
        self.assertEqual(response['statusCode'], 400)

    @patch('app.photos_table')
    def test_photo_not_found(self, mock_table):
        """Test error handling for photo not found"""
        # Mock DynamoDB response for non-existent photo
        mock_table.get_item.return_value = {}  # No Item in response
        
        # Create a test event
        event = {
            'pathParameters': {
                'photoId': 'non-existent-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Photo not found')

    @patch('app.photos_table')
    def test_dynamodb_error(self, mock_table):
        """Test error handling for DynamoDB failure"""
        # Mock DynamoDB to raise an exception
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'DynamoDB error'}},
            'GetItem'
        )
        
        # Create a test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to retrieve photo metadata')

    @patch('app.photos_table')
    @patch('app.s3_client')
    def test_s3_presigned_url_error(self, mock_s3, mock_table):
        """Test error handling for S3 pre-signed URL generation failure"""
        # Mock DynamoDB response
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id.jpg'
            }
        }
        
        # Mock S3 to raise an exception
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'S3 error'}},
            'GeneratePresignedUrl'
        )
        
        # Create a test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to generate download URL')

if __name__ == '__main__':
    unittest.main()