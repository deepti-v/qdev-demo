from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
)
from constructs import Construct
import aws_cdk.aws_apigatewayv2_alpha as apigwv2
import aws_cdk.aws_apigatewayv2_integrations_alpha as apigwv2_integrations

class PhotoAppStack(Stack):
    """
    CDK Stack for the Photo App.
    
    This stack creates:
    - S3 bucket for photo storage
    - DynamoDB table for photo metadata
    - Lambda functions for uploading and retrieving photos
    - API Gateway HTTP API for accessing the Lambda functions
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for photos (private)
        photos_bucket = s3.Bucket(
            self, "PhotosBucket",
            removal_policy=RemovalPolicy.DESTROY,  # For development; use RETAIN for production
            auto_delete_objects=True,  # For development; remove for production
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
        )

        # Create DynamoDB table for photo metadata
        photos_table = dynamodb.Table(
            self, "PhotosTable",
            partition_key=dynamodb.Attribute(
                name="photoId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # For development; use RETAIN for production
        )

        # Create Lambda function for uploading photos
        upload_photo_function = lambda_.Function(
            self, "UploadPhotoFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("../src/upload_photo"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "PHOTOS_TABLE": photos_table.table_name,
                "PHOTOS_BUCKET": photos_bucket.bucket_name,
            },
        )

        # Create Lambda function for retrieving photos
        get_photo_function = lambda_.Function(
            self, "GetPhotoFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("../src/get_photo"),
            timeout=Duration.seconds(10),
            memory_size=128,
            environment={
                "PHOTOS_TABLE": photos_table.table_name,
                "PHOTOS_BUCKET": photos_bucket.bucket_name,
                "URL_EXPIRATION": "3600",  # 1 hour
            },
        )

        # Grant permissions to Lambda functions
        photos_bucket.grant_read_write(upload_photo_function)
        photos_bucket.grant_read(get_photo_function)
        photos_table.grant_write_data(upload_photo_function)
        photos_table.grant_read_data(get_photo_function)

        # Create API Gateway HTTP API
        http_api = apigwv2.HttpApi(
            self, "PhotosApi",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],  # For development; restrict in production
                allow_methods=[apigwv2.CorsHttpMethod.GET, apigwv2.CorsHttpMethod.POST, apigwv2.CorsHttpMethod.OPTIONS],
                allow_headers=["Content-Type"],
                max_age=Duration.days(1),
            ),
        )

        # Add routes to API Gateway
        upload_integration = apigwv2_integrations.HttpLambdaIntegration(
            "UploadPhotoIntegration", upload_photo_function
        )
        http_api.add_routes(
            path="/photos",
            methods=[apigwv2.HttpMethod.POST],
            integration=upload_integration,
        )

        get_integration = apigwv2_integrations.HttpLambdaIntegration(
            "GetPhotoIntegration", get_photo_function
        )
        http_api.add_routes(
            path="/photos/{photoId}",
            methods=[apigwv2.HttpMethod.GET],
            integration=get_integration,
        )