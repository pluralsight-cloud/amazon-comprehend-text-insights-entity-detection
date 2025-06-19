#!/usr/bin/env python3
"""
This script demonstrates how to use Amazon Comprehend for:
1. Sentiment Analysis
2. Entity Detection
"""

import boto3
import json
from botocore.exceptions import ClientError

def detect_sentiment(text, language_code='en'):
    """
    Detects the sentiment of the text using Amazon Comprehend.
    
    Parameters:
    text (str): The text to analyze
    language_code (str): The language code (default: 'en' for English)
    
    Returns:
    dict: The sentiment analysis results
    """
    comprehend = boto3.client('comprehend')
    
    try:
        response = comprehend.detect_sentiment(
            Text=text,
            LanguageCode=language_code
        )
        return response
    except ClientError as e:
        print(f"Error detecting sentiment: {e}")
        return None

def detect_entities(text, language_code='en'):
    """
    Detects entities in the text using Amazon Comprehend.
    
    Parameters:
    text (str): The text to analyze
    language_code (str): The language code (default: 'en' for English)
    
    Returns:
    dict: The entity detection results
    """
    comprehend = boto3.client('comprehend')
    
    try:
        response = comprehend.detect_entities(
            Text=text,
            LanguageCode=language_code
        )
        return response
    except ClientError as e:
        print(f"Error detecting entities: {e}")
        return None

def print_sentiment_results(results):
    """Pretty print sentiment analysis results"""
    if not results:
        return
    
    print("\n=== Sentiment Analysis Results ===")
    print(f"Sentiment: {results['Sentiment']}")
    print("Confidence Scores:")
    for sentiment, score in results['SentimentScore'].items():
        print(f"  {sentiment}: {score:.4f}")

def print_entity_results(results):
    """Pretty print entity detection results"""
    if not results:
        return
    
    print("\n=== Entity Detection Results ===")
    for entity in results['Entities']:
        print(f"Text: {entity['Text']}")
        print(f"Type: {entity['Type']}")
        print(f"Score: {entity['Score']:.4f}")
        print("---")

def main():
    # Sample text for analysis
    sample_text = "On June 4, 2025 Pluralsight, the technology workforce development company, announced that Mathew Ellis was appointed Chief Financial Officer. " \
                 "Pluralsight is headquartered in Draper, Utah with worldwide offices in India, Ireland, and Australia. " \
                 "Amazon Comprehend is a natural language processing service that uses machine learning to automatically process text to find meaning and insights."
    
    print("Amazon Comprehend Demo - Real-time Text Analysis")
    print("-" * 50)
    print(f"Sample text: \"{sample_text}\"")
    
    # Detect sentiment
    sentiment_results = detect_sentiment(sample_text)
    print_sentiment_results(sentiment_results)
    
    # Detect entities
    entity_results = detect_entities(sample_text)
    print_entity_results(entity_results)

if __name__ == "__main__":
    main()
