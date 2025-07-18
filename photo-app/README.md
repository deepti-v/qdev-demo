# Serverless Photo Upload Application

A serverless application for uploading and retrieving photos using AWS services. This application provides a simple web interface for users to upload photos and retrieve them using unique IDs.

## Architecture

![Architecture Diagram](https://via.placeholder.com/800x400?text=Photo+App+Architecture+Diagram)

### Components

- **Frontend**: HTML/CSS/JavaScript web interface
- **API Gateway**: HTTP API with two endpoints:
  - `POST /photos`: Upload a photo and its metadata
  - `GET /photos/{photoId}`: Retrieve a photo by ID
- **Lambda Functions**:
  - `UploadPhotoFunction`: Processes photo uploads, stores in S3, and saves metadata to DynamoDB
  - `GetPhotoFunction`: Retrieves photo metadata from DynamoDB and generates a pre-signed URL for S3 access
- **S3**: Private bucket for secure photo storage
- **DynamoDB**: NoSQL database for storing photo metadata

## Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate permissions
- [AWS CDK](https://aws.amazon.com/cdk/) installed (for CDK deployment)
- [AWS SAM CLI](https://aws.amazon.com/serverless/sam/) installed (for SAM deployment)
- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js 14+](https://nodejs.org/) (for local frontend testing)

## Setup Instructions

### Option 1: Deploy with AWS CDK

1. Install CDK dependencies:
   ```
   cd cdk
   pip install -r requirements.txt
   ```

2. Deploy the application:
   ```
   cdk deploy
   ```

3. Note the API Gateway URL from the CDK outputs.

### Option 2: Deploy with AWS SAM

1. Build the SAM application:
   ```
   sam build
   ```

2. Deploy the application:
   ```
   sam deploy --guided
   ```

3. Follow the prompts and note the API Gateway URL from the outputs.

### Configure the Frontend

1. Open `frontend/script.js` in a text editor.
2. Replace `YOUR_API_GATEWAY_URL` with the actual API Gateway URL from the deployment.
3. Serve the frontend locally for testing:
   ```
   cd frontend
   python -m http.server 8000
   ```
4. Open a browser and navigate to `http://localhost:8000`

## Usage

### Upload a Photo

1. Select a photo file using the file input.
2. Click "Upload Photo".
3. Note the Photo ID returned after successful upload.

### Retrieve a Photo

1. Enter the Photo ID in the input field.
2. Click "Get Photo".
3. The photo will be displayed along with its metadata.
4. Click the "Download Photo" link to download the original file.

## Development

### Project Structure

```
photo-app/
├── src/
│   ├── upload_photo/
│   │   ├── app.py            # Lambda function for uploading photos
│   │   └── requirements.txt  # Python dependencies
│   ├── get_photo/
│   │   ├── app.py            # Lambda function for retrieving photos
│   │   └── requirements.txt  # Python dependencies
├── tests/
│   ├── unit/
│   │   ├── test_upload_photo.py  # Unit tests for upload function
│   │   └── test_get_photo.py     # Unit tests for get function
├── frontend/
│   ├── index.html            # Web interface
│   ├── style.css             # Styling
│   └── script.js             # Frontend logic
├── cdk/
│   ├── app.py                # CDK application entry point
│   ├── photo_app_stack.py    # CDK stack definition
│   └── requirements.txt      # CDK dependencies
├── template.yaml             # SAM/CloudFormation template
└── README.md                 # Documentation
```

### Running Tests

Run unit tests with pytest:
```
pip install pytest
pytest tests/unit/
```

### Local Development

Test Lambda functions locally with SAM:
```
sam local invoke UploadPhotoFunction --event events/upload_event.json
sam local invoke GetPhotoFunction --event events/get_event.json
```

## Security Considerations

- The S3 bucket is configured as private with no public access.
- Lambda functions follow the principle of least privilege with specific IAM permissions.
- API Gateway endpoints use CORS to control access.
- Pre-signed URLs for S3 objects expire after 1 hour.

## Assumptions

- Users will upload reasonably sized images (< 10MB).
- The application is for demonstration purposes and may need additional security measures for production use.
- Frontend is served from a separate hosting service or locally for development.

## License

This project is licensed under the MIT License - see the LICENSE file for details.