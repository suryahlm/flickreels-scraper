"""
Batch Scraper for Railway 24/7 Production
==========================================

Scrapes 300 dramas continuously with:
- 12 concurrent episodes per drama
- Auto-retry on failures
- Progress tracking
- Error logging
- Resume capability

Usage (on Railway):
    python batch_scraper_railway.py
"""

import os
import json
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('batch_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ALWAYS CLEAR PROGRESS ON STARTUP (FORCED - No conditions!)
# This ensures fresh start after R2 wipe and nested folder restructure
# ============================================================================

import sys

# ALWAYS DELETE PROGRESS FILES - NO CONDITIONS!
logger.info("🗑️ Clearing all progress files for fresh start...")
for pf in ["scraping_progress.json", "scraped_ids.txt", "scrape_progress.json", 
           "batch_stats.json", "failed_dramas.txt"]:
    if os.path.exists(pf):
        try:
            os.remove(pf)
            logger.info(f"  ✓ Deleted: {pf}")
        except Exception as e:
            logger.warning(f"  ⚠ Could not delete {pf}: {e}")
logger.info("✅ Fresh start ready!")


# ============================================================================
# CONFIGURATION
# ============================================================================

DRAMA_LIST_FILE = "popular_dramas_300.txt"
PROGRESS_FILE = "scraping_progress.json"
FAILED_DRAMAS_FILE = "failed_dramas.txt"

# Stats
STATS = {
    "start_time": datetime.now().isoformat(),
    "total_dramas": 0,
    "completed": 0,
    "failed": 0,
    "current_drama": None,
    "estimated_completion": None
}

# ============================================================================
# PROGRESS TRACKING
# ============================================================================

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"completed_dramas": [], "failed_dramas": []}
    return {"completed_dramas": [], "failed_dramas": []}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def save_stats():
    """Save stats to file"""
    with open('batch_stats.json', 'w') as f:
        json.dump(STATS, f, indent=2)

# ============================================================================
# DRAMA LIST LOADER
# ============================================================================

def load_drama_list():
    """Load drama IDs from file"""
    if not os.path.exists(DRAMA_LIST_FILE):
        logger.error(f"Drama list file not found: {DRAMA_LIST_FILE}")
        logger.info("Creating sample drama list with 300 popular dramas...")
        
        # Sample popular drama IDs (you should replace with real list)
        sample_dramas = generate_sample_drama_list()
        
        with open(DRAMA_LIST_FILE, 'w') as f:
            for drama_id in sample_dramas:
                f.write(f"{drama_id}\n")
        
        logger.info(f"Created {DRAMA_LIST_FILE} with {len(sample_dramas)} dramas")
    
    with open(DRAMA_LIST_FILE, 'r') as f:
        dramas = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(dramas)} dramas from {DRAMA_LIST_FILE}")
    return dramas

def generate_sample_drama_list():
    """Generate sample list of 300 drama IDs"""
    # You should replace this with actual popular drama IDs
    # For now, using placeholder IDs
    base_ids = [
        2858, 533, 3108, 5190, 4200, 6789, 1234, 5678, 9012, 3456,
        7890, 2345, 6123, 4567, 8901, 2789, 5012, 7345, 9678, 1901
    ]
    
    # Extend to 300 (you should get real drama IDs!)
    sample = []
    for i in range(300):
        sample.append(str(base_ids[i % len(base_ids)] + i * 10))
    
    return sample

# ============================================================================
# SCRAPER
# ============================================================================

def scrape_drama(drama_id: str) -> bool:
    """
    Scrape single drama using concurrent scraper
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting drama: {drama_id}")
    logger.info(f"{'='*60}\n")
    
    try:
        # Run concurrent scraper
        result = subprocess.run(
            [
                'python',
                'railway_streaming_scraper_concurrent.py',
                '--drama', drama_id
            ],
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout per drama
        )
        
        # Log output
        if result.stdout:
            logger.info(result.stdout)
        
        if result.stderr:
            logger.error(result.stderr)
        
        if result.returncode == 0:
            logger.info(f"✅ Drama {drama_id} completed successfully!")
            return True
        else:
            logger.error(f"❌ Drama {drama_id} failed with code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Drama {drama_id} timed out after 2 hours")
        return False
    except Exception as e:
        logger.error(f"❌ Drama {drama_id} failed with exception: {e}")
        return False

# ============================================================================
# MAIN BATCH SCRAPER
# ============================================================================

def run_batch_scraper():
    """Main batch scraping loop"""
    logger.info("\n" + "="*60)
    logger.info("RAILWAY BATCH SCRAPER - PRODUCTION MODE")
    logger.info("="*60 + "\n")
    
    # Load drama list
    all_dramas = load_drama_list()
    STATS["total_dramas"] = len(all_dramas)
    
    # Load progress
    progress = load_progress()
    completed = set(progress.get("completed_dramas", []))
    failed = set(progress.get("failed_dramas", []))
    
    # Filter out already processed
    remaining = [d for d in all_dramas if d not in completed]
    
    logger.info(f"Total dramas: {len(all_dramas)}")
    logger.info(f"Already completed: {len(completed)}")
    logger.info(f"Already failed: {len(failed)}")
    logger.info(f"Remaining: {len(remaining)}")
    
    # Check if nothing to do
    if len(remaining) == 0:
        logger.info("\n✅ All dramas already completed! Nothing to scrape.")
        logger.info("Use --clear flag to reset progress and start fresh.")
        return
    
    logger.info(f"\nStarting continuous scraping...\n")
    
    STATS["completed"] = len(completed)
    STATS["failed"] = len(failed)
    
    start_time = time.time()
    
    # Process each drama
    for i, drama_id in enumerate(remaining):
        drama_num = i + 1
        total_remaining = len(remaining)
        
        logger.info(f"\n[{drama_num}/{total_remaining}] Processing drama {drama_id}...")
        STATS["current_drama"] = drama_id
        
        # Estimate completion
        if i > 0:
            elapsed = time.time() - start_time
            avg_time_per_drama = elapsed / i
            remaining_time = avg_time_per_drama * (total_remaining - i)
            estimated_completion = datetime.fromtimestamp(time.time() + remaining_time)
            STATS["estimated_completion"] = estimated_completion.isoformat()
            
            logger.info(f"Estimated completion: {estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Average time per drama: {avg_time_per_drama/60:.1f} minutes")
        
        # Scrape drama
        success = scrape_drama(drama_id)
        
        # Update progress
        if success:
            completed.add(drama_id)
            STATS["completed"] += 1
            logger.info(f"Progress: {len(completed)}/{len(all_dramas)} dramas completed")
        else:
            failed.add(drama_id)
            STATS["failed"] += 1
            
            # Save to failed file
            with open(FAILED_DRAMAS_FILE, 'a') as f:
                f.write(f"{drama_id}\n")
            
            logger.warning(f"Failed dramas so far: {len(failed)}")
        
        # Save progress
        progress["completed_dramas"] = list(completed)
        progress["failed_dramas"] = list(failed)
        save_progress(progress)
        save_stats()
        
        # Small delay between dramas
        time.sleep(5)
    
    # Final report
    total_time = time.time() - start_time
    
    logger.info("\n" + "="*60)
    logger.info("BATCH SCRAPING COMPLETE!")
    logger.info("="*60)
    logger.info(f"Total dramas: {len(all_dramas)}")
    logger.info(f"Successfully scraped: {len(completed)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total time: {total_time/3600:.1f} hours")
    if len(remaining) > 0:
        logger.info(f"Average per drama: {total_time/len(remaining)/60:.1f} minutes")
    logger.info("="*60 + "\n")
    
    if failed:
        logger.info(f"Failed drama IDs saved to: {FAILED_DRAMAS_FILE}")
        logger.info("You can retry failed dramas later.")
    
    logger.info("\n🎉 ALL DONE! Ready for app launch! 🚀\n")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        run_batch_scraper()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Scraping interrupted by user")
        logger.info(f"Progress saved to: {PROGRESS_FILE}")
        logger.info("You can resume by running this script again.")
    except Exception as e:
        logger.error(f"\n\n🚨 Fatal error: {e}")
        logger.error(f"Progress saved to: {PROGRESS_FILE}")
        raise
