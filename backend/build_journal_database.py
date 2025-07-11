#!/usr/bin/env python3
"""
Script to download SCImago journal data and create a local database file.
Run this once to create the journal database, then the main app can use the local file.
"""

import requests
import csv
import io
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_scimago_subjects(categories: str) -> str:
    """Extract main subject areas from SCImago categories string"""
    if not categories:
        return None
        
    # Categories format: "Subject1 (Q1); Subject2 (Q2); ..."
    # Extract just the subject names without quartiles
    subjects = []
    for category in categories.split(';'):
        # Remove quartile info (Q1), (Q2), etc. and clean
        subject = category.split('(')[0].strip()
        if subject:
            subjects.append(subject)
    
    # Return primary subject (first one) for simplicity
    return subjects[0] if subjects else None

def download_scimago_data():
    """Download journal data from SCImago and create local database"""
    
    logger.info("Downloading SCImago journal data...")
    
    url = "https://www.scimagojr.com/journalrank.php"
    params = {
        'out': 'xls',
        'year': '2023',
        'min': '0',
        'max': '50000'  # Get all journals
    }
    
    try:
        response = requests.get(url, params=params, timeout=120)
        if response.status_code != 200:
            logger.error(f"SCImago request failed with status {response.status_code}")
            return None
            
        logger.info(f"Downloaded {len(response.text)} characters of data")
        
        # Parse CSV data
        csv_data = io.StringIO(response.text)
        reader = csv.DictReader(csv_data, delimiter=';')
        
        journal_database = {}
        subject_areas = set()
        
        count = 0
        for row in reader:
            journal_name = row.get('Title', '').strip().lower()
            categories = row.get('Categories', '').strip()
            
            if journal_name and categories:
                # Extract main subject
                main_subject = extract_scimago_subjects(categories)
                if main_subject:
                    journal_database[journal_name] = {
                        'subject': main_subject,
                        'categories': categories,
                        'rank': row.get('Rank', ''),
                        'sjr': row.get('SJR', ''),
                        'h_index': row.get('H index', '')
                    }
                    subject_areas.add(main_subject)
                    count += 1
        
        logger.info(f"Processed {count} journals")
        logger.info(f"Found {len(subject_areas)} unique subject areas")
        
        # Create database structure
        database = {
            'metadata': {
                'source': 'SCImago Journal Rank',
                'year': '2023',
                'download_date': datetime.now().isoformat(),
                'total_journals': count,
                'subject_areas': sorted(list(subject_areas))
            },
            'journals': journal_database
        }
        
        return database
        
    except Exception as e:
        logger.error(f"Error downloading SCImago data: {e}")
        return None

def save_database(database, filename="scimago_journals.json"):
    """Save the journal database to a JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved journal database to {filename}")
        logger.info(f"Total journals: {database['metadata']['total_journals']}")
        logger.info(f"Subject areas: {len(database['metadata']['subject_areas'])}")
        
        # Print some sample subject areas
        logger.info("Sample subject areas:")
        for i, subject in enumerate(database['metadata']['subject_areas'][:10]):
            logger.info(f"  {i+1}. {subject}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving database: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting SCImago journal database creation...")
    
    # Download data
    database = download_scimago_data()
    
    if database:
        # Save to local file
        if save_database(database):
            logger.info("Journal database created successfully!")
        else:
            logger.error("Failed to save database")
    else:
        logger.error("Failed to download SCImago data")