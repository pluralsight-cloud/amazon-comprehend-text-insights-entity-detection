#!/usr/bin/env python3
"""
Amazon Comprehend Topic Modeling Example
This script demonstrates how to use Amazon Comprehend for topic modeling
with sample data created within the script.
"""

import boto3
import json
import time
import uuid
import os
from datetime import datetime

def create_sample_data():
    """Create sample documents for topic modeling"""
    
    # Create a directory for our sample data
    data_dir = "sample_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Sample documents with different topics
    documents = [
        # Technology documents
        "Machine learning models require large amounts of data for training. Neural networks have revolutionized AI development.",
        "Cloud computing provides scalable resources for businesses. AWS offers a wide range of services for developers.",
        "Blockchain technology ensures secure and transparent transactions. Cryptocurrencies use distributed ledger systems.",
        "Mobile applications are essential for modern businesses. User experience design is critical for app success.",
        
        # Finance documents
        "Stock markets fluctuate based on economic indicators. Investors analyze company performance before making decisions.",
        "Banking regulations ensure financial stability. Interest rates affect borrowing and lending activities.",
        "Investment portfolios should be diversified to minimize risk. Retirement planning requires long-term financial strategy.",
        "Corporate finance involves capital structure decisions. Financial statements provide insights into company health.",
        
        # Healthcare documents
        "Medical research advances treatment options for patients. Clinical trials test the efficacy of new medications.",
        "Healthcare systems face challenges with aging populations. Preventive care reduces long-term medical costs.",
        "Telemedicine expands access to healthcare services. Electronic health records improve patient care coordination.",
        "Mental health awareness has increased in recent years. Holistic approaches consider physical and psychological wellbeing."
    ]
    
    # Write each document to a separate file
    file_paths = []
    for i, doc in enumerate(documents):
        file_path = f"{data_dir}/document_{i}.txt"
        with open(file_path, "w") as f:
            f.write(doc)
        file_paths.append(file_path)
    
    return data_dir, file_paths

def upload_to_s3(bucket_name, data_dir):
    """Upload sample data to S3 bucket"""
    
    s3 = boto3.client('s3')
    
    # Create a unique bucket if one isn't provided
    if not bucket_name:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        bucket_name = f"comprehend-topic-modeling-{timestamp}-{str(uuid.uuid4())[:8]}"
        try:
            s3.create_bucket(Bucket=bucket_name)
            print(f"Created S3 bucket: {bucket_name}")
        except Exception as e:
            print(f"Error creating bucket: {e}")
            return None
    
    # Upload all files from the data directory
    input_s3_path = f"s3://{bucket_name}/input/"
    for root, _, files in os.walk(data_dir):
        for file in files:
            local_path = os.path.join(root, file)
            s3_key = f"input/{file}"
            s3.upload_file(local_path, bucket_name, s3_key)
    
    print(f"Uploaded sample data to {input_s3_path}")
    return bucket_name, input_s3_path

def start_topic_modeling_job(bucket_name, input_s3_path):
    """Start an Amazon Comprehend topic modeling job"""
    
    comprehend = boto3.client('comprehend')
    
    # Create a unique job name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    job_name = f"topic-modeling-job-{timestamp}"
    
    # Output location
    output_s3_path = f"s3://{bucket_name}/output/"
    
    # Start the topic modeling job
    try:
        response = comprehend.start_topics_detection_job(
            InputDataConfig={
                'S3Uri': input_s3_path,
                'InputFormat': 'ONE_DOC_PER_FILE'
            },
            OutputDataConfig={
                'S3Uri': output_s3_path
            },
            DataAccessRoleArn=get_comprehend_role_arn(),
            JobName=job_name,
            NumberOfTopics=3  # We expect 3 topics: Technology, Finance, Healthcare
        )
        
        job_id = response['JobId']
        print(f"Started topic modeling job: {job_id}")
        return job_id, output_s3_path
    
    except Exception as e:
        print(f"Error starting topic modeling job: {e}")
        return None, None

def get_comprehend_role_arn():
    """Create or get an IAM role for Comprehend to access S3"""
    
    iam = boto3.client('iam')
    role_name = "ComprehendTopicModelingRole"
    
    # Check if the role already exists
    try:
        response = iam.get_role(RoleName=role_name)
        print(f"Using existing role: {role_name}")
        return response['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        print(f"Creating new role: {role_name}")
        
        # Create the trust policy for Comprehend
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "comprehend.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create the role
        try:
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Amazon Comprehend to access S3 for topic modeling"
            )
            
            # Create policy to allow S3 access
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:ListBucket",
                            "s3:PutObject"
                        ],
                        "Resource": [
                            "arn:aws:s3:::*"
                        ]
                    }
                ]
            }
            
            # Attach the policy to the role
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName="ComprehendS3Access",
                PolicyDocument=json.dumps(policy_document)
            )
            
            # Wait a few seconds for the role to be fully available
            print("Waiting for role to be fully available...")
            time.sleep(10)
            
            return role['Role']['Arn']
        except Exception as e:
            print(f"Error creating role: {e}")
            print("Please provide an existing role ARN with proper permissions")
            role_arn = input("Enter your Comprehend service role ARN: ")
            return role_arn

def check_job_status(job_id):
    """Check the status of a topic modeling job"""
    
    comprehend = boto3.client('comprehend')
    
    while True:
        response = comprehend.describe_topics_detection_job(JobId=job_id)
        status = response['TopicsDetectionJobProperties']['JobStatus']
        
        print(f"Job status: {status}")
        
        if status in ['COMPLETED', 'FAILED', 'STOPPED']:
            return status, response
        
        # Wait before checking again
        time.sleep(30)

def get_job_results(bucket_name, job_id, output_s3_path):
    """Get the results of a completed topic modeling job"""
    
    s3 = boto3.client('s3')
    
    # The output will be in a directory named with the job ID
    try:
        # List objects in the output path
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=f"output/{job_id}/output"
        )
        
        # Find the topic-terms file
        topic_terms_file = None
        for obj in response.get('Contents', []):
            if 'topic-terms' in obj['Key']:
                topic_terms_file = obj['Key']
                break
        
        if topic_terms_file:
            # Download the topic terms file
            local_file = "topic_terms.csv"
            s3.download_file(bucket_name, topic_terms_file, local_file)
            print(f"Downloaded topic terms to {local_file}")
            
            # Display the first few lines of the file
            print("\nTopic modeling results (top terms for each topic):")
            with open(local_file, 'r') as f:
                for i, line in enumerate(f):
                    print(line.strip())
                    if i >= 10:  # Show first 10 lines
                        break
        else:
            print("Topic terms file not found in output")
    
    except Exception as e:
        print(f"Error retrieving results: {e}")

def main():
    """Main function to run the topic modeling example"""
    
    print("Amazon Comprehend Topic Modeling Example")
    print("----------------------------------------")
    
    # Step 1: Create sample data
    print("\nStep 1: Creating sample data...")
    data_dir, file_paths = create_sample_data()
    print(f"Created {len(file_paths)} sample documents in {data_dir}/")
    
    # Step 2: Upload data to S3
    print("\nStep 2: Uploading data to S3...")
    bucket_name = None  # Will create a unique bucket
    bucket_name, input_s3_path = upload_to_s3(bucket_name, data_dir)
    
    if not bucket_name:
        print("Failed to upload data to S3. Exiting.")
        return
    
    # Step 3: Start topic modeling job
    print("\nStep 3: Starting topic modeling job...")
    job_id, output_s3_path = start_topic_modeling_job(bucket_name, input_s3_path)
    
    if not job_id:
        print("Failed to start topic modeling job. Exiting.")
        return
    
    # Step 4: Wait for job completion
    print("\nStep 4: Waiting for job completion...")
    status, response = check_job_status(job_id)
    
    if status != 'COMPLETED':
        print(f"Job did not complete successfully. Status: {status}")
        return
    
    # Step 5: Get results
    print("\nStep 5: Getting job results...")
    get_job_results(bucket_name, job_id, output_s3_path)
    
    print("\nTopic modeling complete!")
    print(f"Full results are available in S3: {output_s3_path}{job_id}/")
    print("\nNote: In a production environment, remember to clean up resources:")
    print(f"- S3 bucket: {bucket_name}")

if __name__ == "__main__":
    main()
