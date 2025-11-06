#!/usr/bin/env python3
"""
Background Batch Monitor - Automatic Batch Processing

This script runs continuously in the background and:
1. Polls active batches every 5 minutes
2. Checks batch status in Anthropic API
3. Automatically retrieves and processes results when complete
4. Logs all activity for debugging

Usage:
    # Run in background
    python utilities/batch_monitor.py &

    # Run with custom poll interval (seconds)
    python utilities/batch_monitor.py --interval 300

    # Run once (no continuous polling)
    python utilities/batch_monitor.py --once
"""

import sys
import os
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import DatabaseManager
from src.data.unified_bulk_processor import UnifiedBulkProcessor

# Setup logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "batch_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BatchMonitor:
    """Monitors and processes batch jobs automatically"""

    def __init__(self, poll_interval: int = 300):
        """
        Initialize batch monitor

        Args:
            poll_interval: Seconds between status checks (default 300 = 5 minutes)
        """
        self.poll_interval = poll_interval
        self.db = DatabaseManager()
        self.processor = None

        # Initialize processor with API key check
        try:
            self.processor = UnifiedBulkProcessor()
            logger.info(f"✅ Batch monitor initialized (poll interval: {poll_interval}s)")
        except ValueError as e:
            logger.error(f"❌ Failed to initialize: {e}")
            logger.error("💡 Set ANTHROPIC_API_KEY or NEWS_API_KEY environment variable")
            raise

    def get_active_batches(self):
        """Get list of active batch IDs from database"""
        try:
            if not self.db.connect():
                logger.error("❌ Failed to connect to database")
                return []

            batch_ids = self.db.get_active_batch_ids()
            self.db.close()

            return batch_ids
        except Exception as e:
            logger.error(f"❌ Error getting active batches: {str(e)}")
            return []

    def check_and_process_batch(self, batch_id: str) -> bool:
        """
        Check batch status and process if complete

        Args:
            batch_id: Anthropic batch ID

        Returns:
            True if batch was processed, False otherwise
        """
        try:
            # Check status
            logger.info(f"🔍 Checking status for batch {batch_id[:20]}...")
            status = self.processor.check_batch_status(batch_id)

            if not status or not status.get('success'):
                logger.warning(f"⚠️ Could not check status for batch {batch_id[:20]}")
                return False

            batch_status = status.get('status')
            completed = status.get('completed_count', 0)
            total = status.get('submitted_count', 0)

            logger.info(f"📊 Batch {batch_id[:20]}: {batch_status} ({completed}/{total})")

            # If batch is complete, process results
            if batch_status == 'ended':
                logger.info(f"🎉 Batch {batch_id[:20]} completed! Processing results...")

                result = self.processor.retrieve_and_process_batch_results(batch_id)

                if result and result.get('success'):
                    successful = result.get('successful_updates', 0)
                    failed = result.get('failed_updates', 0)

                    logger.info(f"✅ Processed batch {batch_id[:20]}")
                    logger.info(f"   📈 Successful: {successful}")
                    logger.info(f"   ❌ Failed: {failed}")

                    return True
                else:
                    error = result.get('error', 'Unknown error') if result else 'No result returned'
                    logger.error(f"❌ Failed to process batch {batch_id[:20]}: {error}")
                    return False

            elif batch_status == 'in_progress':
                logger.info(f"⏳ Batch {batch_id[:20]} still processing ({completed}/{total})...")
                return False

            elif batch_status == 'processing':
                logger.info(f"⏳ Batch {batch_id[:20]} is being processed by Anthropic...")
                return False

            else:
                logger.warning(f"⚠️ Batch {batch_id[:20]} has unexpected status: {batch_status}")
                return False

        except Exception as e:
            logger.error(f"❌ Error processing batch {batch_id[:20]}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def poll_once(self):
        """Run a single poll cycle"""
        logger.info("=" * 80)
        logger.info(f"🔄 Polling cycle started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        # Get active batches
        active_batches = self.get_active_batches()

        if not active_batches:
            logger.info("📭 No active batches to monitor")
            return

        logger.info(f"📦 Found {len(active_batches)} active batch(es)")

        # Process each batch
        processed_count = 0
        for batch_id in active_batches:
            if self.check_and_process_batch(batch_id):
                processed_count += 1

        if processed_count > 0:
            logger.info(f"✅ Successfully processed {processed_count} batch(es)")

        logger.info("=" * 80)
        logger.info(f"✓ Poll cycle complete")
        logger.info("=" * 80)

    def run_continuous(self):
        """Run continuous monitoring loop"""
        logger.info("🚀 Starting continuous batch monitor...")
        logger.info(f"⏱️  Poll interval: {self.poll_interval} seconds")
        logger.info(f"📁 Log file: {log_dir / 'batch_monitor.log'}")
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("")

        try:
            while True:
                try:
                    self.poll_once()
                except Exception as e:
                    logger.error(f"❌ Error in poll cycle: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

                # Wait before next poll
                logger.info(f"💤 Sleeping for {self.poll_interval} seconds...")
                logger.info("")
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("")
            logger.info("🛑 Batch monitor stopped by user")
            logger.info("✓ Exiting gracefully...")


def main():
    parser = argparse.ArgumentParser(
        description="Background batch monitor for automatic result processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default 5-minute interval
  python utilities/batch_monitor.py

  # Run with 10-minute interval
  python utilities/batch_monitor.py --interval 600

  # Run once (no continuous polling)
  python utilities/batch_monitor.py --once

  # Run in background (Unix/Mac)
  nohup python utilities/batch_monitor.py > /dev/null 2>&1 &
        """
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Poll interval in seconds (default: 300 = 5 minutes)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (no continuous polling)'
    )

    args = parser.parse_args()

    try:
        monitor = BatchMonitor(poll_interval=args.interval)

        if args.once:
            logger.info("🔄 Running single poll cycle...")
            monitor.poll_once()
            logger.info("✓ Single poll complete")
        else:
            monitor.run_continuous()

    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
