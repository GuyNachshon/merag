#!/usr/bin/env python3
"""
Test script for periodic indexing functionality
This script demonstrates how the periodic indexer works by placing test files in the watch directory.
"""

import asyncio
import logging
import time
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_test_files():
    """Create test files in the watch directory"""
    watch_dir = Path("./storage/watch")
    watch_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some test text files
    test_files = [
        {
            "name": "test_document_1.txt",
            "content": """
מסמך בדיקה ראשון
זהו מסמך בדיקה בעברית לבדיקת מערכת האינדוקס האוטומטי.
המערכת אמורה לזהות את המסמך החדש ולהוסיף אותו לבסיס הנתונים.
            """.strip()
        },
        {
            "name": "test_document_2.txt", 
            "content": """
מסמך בדיקה שני
זהו מסמך נוסף לבדיקת המערכת.
המסמך מכיל מידע נוסף על המערכת ועל איך היא עובדת.
            """.strip()
        },
        {
            "name": "english_test.txt",
            "content": """
English Test Document
This is a test document in English to verify the system works with multiple languages.
The system should process this document and add it to the knowledge base.
            """.strip()
        }
    ]
    
    created_files = []
    for test_file in test_files:
        file_path = watch_dir / test_file["name"]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(test_file["content"])
        created_files.append(file_path)
        logger.info(f"Created test file: {file_path}")
    
    return created_files

async def monitor_indexer_status():
    """Monitor the indexer status"""
    try:
        import requests
        
        # Wait a bit for the indexer to process files
        logger.info("Waiting for indexer to process files...")
        await asyncio.sleep(35)  # Wait longer than scan interval
        
        # Check indexer status
        response = requests.get("http://localhost:8000/api/v1/indexer/status")
        if response.status_code == 200:
            status = response.json()
            logger.info(f"Indexer status: {status}")
        else:
            logger.error(f"Failed to get indexer status: {response.status_code}")
            
        # Check document stats
        response = requests.get("http://localhost:8000/api/v1/documents/stats")
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"Document stats: {stats}")
        else:
            logger.error(f"Failed to get document stats: {response.status_code}")
            
    except ImportError:
        logger.warning("requests not available, skipping status check")
    except Exception as e:
        logger.error(f"Error monitoring status: {e}")

async def main():
    """Main test function"""
    logger.info("Starting periodic indexing test...")
    
    # Create test files
    test_files = await create_test_files()
    logger.info(f"Created {len(test_files)} test files")
    
    # Monitor the process
    await monitor_indexer_status()
    
    logger.info("Test completed!")
    logger.info("Check the logs to see if files were processed by the indexer")

if __name__ == "__main__":
    asyncio.run(main()) 