import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional
import hashlib

from config import settings
from services.rag_agent import rag_service

logger = logging.getLogger(__name__)

class PeriodicIndexer:
    """Service for periodically indexing files from a watched directory"""
    
    def __init__(self):
        self.watch_directory = Path(settings.watch_directory)
        self.processed_files_db = Path(settings.processed_files_db)
        self.scan_interval = settings.scan_interval_seconds
        self.enabled = settings.enable_periodic_indexing
        self.processed_files: Set[str] = set()
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the periodic indexer"""
        if not self.enabled:
            logger.info("Periodic indexing is disabled")
            return
            
        try:
            # Ensure watch directory exists
            self.watch_directory.mkdir(parents=True, exist_ok=True)
            
            # Load processed files database
            await self._load_processed_files()
            
            logger.info(f"Periodic indexer initialized. Watching directory: {self.watch_directory}")
            logger.info(f"Scan interval: {self.scan_interval} seconds")
            
        except Exception as e:
            logger.error(f"Failed to initialize periodic indexer: {e}")
            raise
    
    async def start(self):
        """Start the periodic indexing task"""
        if not self.enabled:
            logger.info("Periodic indexing is disabled, not starting")
            return
            
        if self.running:
            logger.warning("Periodic indexer is already running")
            return
            
        try:
            self.running = True
            self.task = asyncio.create_task(self._indexing_loop())
            logger.info("Periodic indexer started")
            
        except Exception as e:
            logger.error(f"Failed to start periodic indexer: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the periodic indexing task"""
        if not self.running:
            return
            
        try:
            self.running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            logger.info("Periodic indexer stopped")
            
        except Exception as e:
            logger.error(f"Error stopping periodic indexer: {e}")
    
    async def _indexing_loop(self):
        """Main indexing loop"""
        while self.running:
            try:
                await self._scan_and_index()
                await asyncio.sleep(self.scan_interval)
                
            except asyncio.CancelledError:
                logger.info("Indexing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in indexing loop: {e}")
                await asyncio.sleep(self.scan_interval)
    
    async def _scan_and_index(self):
        """Scan directory for new files and index them"""
        try:
            # Get all files in watch directory
            new_files = []
            
            for file_path in self.watch_directory.rglob("*"):
                if file_path.is_file():
                    # Check if file is supported
                    if file_path.suffix.lower() in settings.supported_extensions:
                        # Generate file hash for tracking
                        file_hash = await self._get_file_hash(file_path)
                        
                        # Check if file was already processed
                        if file_hash not in self.processed_files:
                            new_files.append((file_path, file_hash))
            
            if new_files:
                logger.info(f"Found {len(new_files)} new files to index")
                await self._process_new_files(new_files)
            else:
                logger.debug("No new files found")
                
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
    
    async def _process_new_files(self, new_files):
        """Process new files and add them to the knowledge base"""
        try:
            file_paths = [file_path for file_path, _ in new_files]
            file_hashes = [file_hash for _, file_hash in new_files]
            
            # Process files using RAG service
            result = await rag_service.add_documents_from_files([str(fp) for fp in file_paths])
            
            if result["success"]:
                # Mark files as processed
                for file_hash in file_hashes:
                    self.processed_files.add(file_hash)
                
                # Save processed files database
                await self._save_processed_files()
                
                logger.info(f"Successfully indexed {result['files_processed']} files")
                logger.info(f"Added {result['documents_added']} document chunks")
                
                # Optionally move or delete processed files
                await self._cleanup_processed_files(file_paths)
                
            else:
                logger.error(f"Failed to index files: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error processing new files: {e}")
    
    async def _cleanup_processed_files(self, file_paths):
        """Clean up processed files (move to archive or delete)"""
        try:
            for file_path in file_paths:
                try:
                    # For now, just delete the file
                    # You could modify this to move files to an archive directory
                    file_path.unlink()
                    logger.debug(f"Deleted processed file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
    
    async def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash for file to track if it was processed"""
        try:
            # Use file modification time and size for quick hash
            stat = file_path.stat()
            hash_input = f"{file_path.name}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating file hash for {file_path}: {e}")
            # Fallback to filename
            return hashlib.md5(file_path.name.encode()).hexdigest()
    
    async def _load_processed_files(self):
        """Load processed files database"""
        try:
            if self.processed_files_db.exists():
                with open(self.processed_files_db, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get("processed_files", []))
                logger.info(f"Loaded {len(self.processed_files)} processed files from database")
            else:
                self.processed_files = set()
                logger.info("No processed files database found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading processed files database: {e}")
            self.processed_files = set()
    
    async def _save_processed_files(self):
        """Save processed files database"""
        try:
            data = {
                "processed_files": list(self.processed_files),
                "last_updated": datetime.utcnow().isoformat(),
                "total_processed": len(self.processed_files)
            }
            
            with open(self.processed_files_db, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.processed_files)} processed files to database")
            
        except Exception as e:
            logger.error(f"Error saving processed files database: {e}")
    
    async def get_status(self) -> Dict:
        """Get status of the periodic indexer"""
        return {
            "enabled": self.enabled,
            "running": self.running,
            "watch_directory": str(self.watch_directory),
            "scan_interval": self.scan_interval,
            "processed_files_count": len(self.processed_files),
            "last_scan": getattr(self, '_last_scan', None)
        }
    
    async def force_scan(self):
        """Force an immediate scan of the directory"""
        if not self.enabled:
            logger.warning("Periodic indexing is disabled")
            return
            
        logger.info("Forcing immediate directory scan")
        await self._scan_and_index()

# Global periodic indexer instance
periodic_indexer = PeriodicIndexer() 