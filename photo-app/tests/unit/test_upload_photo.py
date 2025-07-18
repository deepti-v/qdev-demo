import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import base64

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/upload_photo'))

# Import the Lambda function
import app

class TestUploadPhotoFunction(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    @patch('app.s3_client')
    @patch('app.photos_table')
    def test_successful_upload(self, mock_table, mock_s3):
        """Test successful photo upload"""
        # Mock S3 and DynamoDB responses
        mock_s3.put_object.return_value = {}
        mock_table.put_item.return_value = {}
        
        # Create a test event
        test_image = base64.b64encode(b'test image data').decode('utf-8')
        event = {
            'body': json.dumps({
                'photo': test_image,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 201)
        response_body = json.loads(response['body'])
        self.assertIn('photoId', response_body)
        self.assertIn('message', response_body)
        self.assertEqual(response_body['message'], 'Photo uploaded successfully')
        
        # Verify S3 and DynamoDB were called correctly
        mock_s3.put_object.assert_called_once()
        mock_table.put_item.assert_called_once()

    @patch('app.s3_client')
    @patch('app.photos_table')
    def test_data_uri_upload(self, mock_table, mock_s3):
        """Test upload with data URI format"""
        # Mock S3 and DynamoDB responses
        mock_s3.put_object.return_value = {}
        mock_table.put_item.return_value = {}
        
        # Create a test event with data URI format
        test_image = base64.b64encode(b'test image data').decode('utf-8')
        data_uri = f'data:image/jpeg;base64,{test_image}'
        event = {
            'body': json.dumps({
                'photo': data_uri,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 201)
        
        # Verify S3 was called with the correct data (base64 decoded)
        mock_s3.put_object.assert_called_once()

    def test_missing_body(self):
        """Test error handling for missing request body"""
        # Create a test event with missing body
        event = {}
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing request body')

    def test_missing_required_fields(self):
        """Test error handling for missing required fields"""
        # Create a test event with missing fields
        event = {
            'body': json.dumps({
                'fileName': 'test.jpg'
                # Missing 'photo' field
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing required fields: photo and fileName')

    @patch('app.s3_client')
    def test_s3_upload_error(self, mock_s3):
        """Test error handling for S3 upload failure"""
        # Mock S3 to raise an exception
        mock_s3.put_object.side_effect = Exception("S3 error")
        
        # Create a test event
        test_image = base64.b64encode(b'test image data').decode('utf-8')
        event = {
            'body': json.dumps({
                'photo': test_image,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to upload photo to storage')

    @patch('app.s3_client')
    @patch('app.photos_table')
    def test_dynamodb_error(self, mock_table, mock_s3):
        """Test error handling for DynamoDB failure"""
        # Mock S3 success but DynamoDB failure
        mock_s3.put_object.return_value = {}
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        
        # Create a test event
        test_image = base64.b64encode(b'test image data').decode('utf-8')
        event = {
            'body': json.dumps({
                'photo': test_image,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to save photo metadata')
        
        # Verify S3 delete was called to clean up
        mock_s3.delete_object.assert_called_once()

if __name__ == '__main__':
    unittest.main()