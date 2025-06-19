#!/usr/bin/env python3
"""
Amazon Comprehend Asynchronous Classification Demo

This script demonstrates how to use Amazon Comprehend for asynchronous text classification
using the AWS SDK for Python (Boto3).
"""

import boto3
import time
import json
import sys
import os
from datetime import datetime

def get_cloudformation_outputs(stack_name):
    """Get outputs from CloudFormation stack"""
    cfn_client = boto3.client('cloudformation')
    response = cfn_client.describe_stacks(StackName=stack_name)
    
    outputs = {}
    for output in response['Stacks'][0]['Outputs']:
        outputs[output['ExportName']] = output['OutputValue']
    
    return outputs

def wait_for_job_completion(comprehend_client, job_id):
    """Wait for a Comprehend job to complete"""
    print(f"Waiting for job {job_id} to complete...")
    
    while True:
        response = comprehend_client.describe_sentiment_detection_job(
            JobId=job_id
        )
        
        status = response['SentimentDetectionJobProperties']['JobStatus']
        print(f"Job {job_id} status: {status}")
        
        if status == 'COMPLETED':
            print("Job completed successfully!")
            return True
        elif status in ['FAILED', 'STOPPED', 'STOP_REQUESTED']:
            print(f"Job did not complete successfully. Final status: {status}")
            if 'Message' in response['SentimentDetectionJobProperties']:
                print(f"Error message: {response['SentimentDetectionJobProperties']['Message']}")
            return False
        
        # Wait before checking again
        time.sleep(30)

def ensure_input_folder_exists(s3_client, bucket_name):
    """Ensure the input folder exists in the S3 bucket"""
    try:
        # Check if the input folder exists
        s3_client.head_object(Bucket=bucket_name, Key='input/')
        print("Input folder exists in S3 bucket.")
    except:
        # Create the input folder if it doesn't exist
        print("Creating input folder in S3 bucket...")
        s3_client.put_object(Bucket=bucket_name, Key='input/')
        print("Input folder created.")

def run_async_classification_job(comprehend_client, bucket_name, role_arn):
    """Run an asynchronous classification job using the built-in sentiment classifier"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    job_name = f"sentiment-classification-job-{timestamp}"
    
    print(f"\nStarting asynchronous classification job: {job_name}")
    
    # start_sentiment_detection_job is the API call that initiates an asynchronous sentiment analysis job
    response = comprehend_client.start_sentiment_detection_job(
        InputDataConfig={
            'S3Uri': f"s3://{bucket_name}/input/",
            'InputFormat': 'ONE_DOC_PER_LINE'
        },
        OutputDataConfig={
            'S3Uri': f"s3://{bucket_name}/output/"
        },
        DataAccessRoleArn=role_arn,
        JobName=job_name,
        LanguageCode='en'
    )
    
    job_id = response['JobId']
    print(f"Classification job started with ID: {job_id}")
    
    # Wait for job to complete
    wait_for_job_completion(comprehend_client, job_id)
    
    return job_id

def main():
    """Main function"""
    print("Amazon Comprehend Asynchronous Classification Demo")
    print("=" * 50)
    
    # Get stack name from command line or use default
    stack_name = "comprehend-async-classification"
    if len(sys.argv) > 1:
        stack_name = sys.argv[1]
    
    try:
        # Get CloudFormation outputs
        print(f"Getting outputs from CloudFormation stack: {stack_name}")
        outputs = get_cloudformation_outputs(stack_name)
        
        bucket_name = outputs['ComprehendAsyncBucketName']
        role_arn = outputs['ComprehendServiceRoleArn']
        
        print(f"S3 Bucket: {bucket_name}")
        print(f"IAM Role ARN: {role_arn}")
        
        # Create clients
        comprehend_client = boto3.client('comprehend')
        s3_client = boto3.client('s3')
        
        # Ensure input folder exists
        ensure_input_folder_exists(s3_client, bucket_name)
        
        # Check if sample file exists in S3
        try:
            s3_client.head_object(Bucket=bucket_name, Key='input/sample_documents.txt')
            print("Sample documents found in S3 bucket.")
        except:
            print("\nSample documents not found in S3 bucket.")
            print("Please upload the sample_documents.txt file to the input folder:")
            print(f"aws s3 cp sample_documents.txt s3://{bucket_name}/input/")
            return
        
        # Run asynchronous classification job
        job_id = run_async_classification_job(comprehend_client, bucket_name, role_arn)
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nMake sure the CloudFormation stack has been deployed successfully.")
        print("You can deploy it using:")
        print("aws cloudformation deploy --template-file comprehend-async-classification.yaml --stack-name comprehend-async-classification --capabilities CAPABILITY_NAMED_IAM")

if __name__ == "__main__":
    main()
