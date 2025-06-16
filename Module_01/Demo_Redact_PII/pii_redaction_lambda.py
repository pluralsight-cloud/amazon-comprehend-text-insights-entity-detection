import boto3
import json
import os
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Comprehend client
comprehend = boto3.client('comprehend')

def redact_pii(text, pii_entities):
    """
    Redact PII entities from the input text.
    
    Args:
        text (str): The original text
        pii_entities (list): List of PII entities detected by Comprehend
        
    Returns:
        str: Text with PII entities redacted
    """
    # Sort entities by their position in descending order to avoid offset issues
    sorted_entities = sorted(pii_entities, key=lambda x: x['BeginOffset'], reverse=True)
    
    # Create a mutable version of the text
    redacted_text = text
    
    # Replace each entity with its type
    for entity in sorted_entities:
        begin = entity['BeginOffset']
        end = entity['EndOffset']
        entity_type = entity['Type']
        
        # Replace the entity with a placeholder
        redacted_text = redacted_text[:begin] + f"[{entity_type}]" + redacted_text[end:]
    
    return redacted_text

def lambda_handler(event, context):
    """
    Lambda function handler to detect and redact PII from input text.
    
    Args:
        event (dict): Lambda event containing 'text' to analyze
        context (LambdaContext): Lambda context
        
    Returns:
        dict: Response with original text, detected entities, and redacted text
    """
    try:
        # Get the text from the event
        if 'text' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No text provided in the event'})
            }
        
        input_text = event['text']
        
        # Check if text is empty
        if not input_text.strip():
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Empty text provided'})
            }
        
        # Check if text exceeds Comprehend's limits (100KB)
        if len(input_text.encode('utf-8')) > 100000:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Text exceeds maximum size of 100KB'})
            }
        
        # Detect PII entities
        logger.info("Detecting PII entities")
        response = comprehend.detect_pii_entities(
            Text=input_text,
            LanguageCode='en'
        )
        
        # Get the PII entities
        pii_entities = response['Entities']
        
        # Redact the PII entities
        redacted_text = redact_pii(input_text, pii_entities)
        
        # Return the results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'originalText': input_text,
                'detectedEntities': pii_entities,
                'redactedText': redacted_text
            })
        }
    
    except ClientError as e:
        logger.error(f"AWS error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"AWS error: {str(e)}"})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Unexpected error: {str(e)}"})
        }
