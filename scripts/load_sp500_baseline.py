#!/usr/bin/env python3
"""
S&P 500 Baseline Data Load Script
Comprehensive data collection for initial baseline establishment
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.collectors import DataCollectionOrchestrator
from src.data.stock_universe import StockUniverseManager
from src.data.database import DatabaseManager
from src.data.database_operations import DatabaseOperationsManager


def setup_logging():
    """Setup logging for the data load process"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'data/sp500_load_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def progress_callback(current: int, total: int, symbol: str):
    """Progress callback for data collection"""
    percentage = (current / total) * 100
    elapsed_time = time.time() - progress_callback.start_time
    
    if current > 0:
        estimated_total_time = elapsed_time * total / current
        remaining_time = estimated_total_time - elapsed_time
        
        print(f"\r📊 Progress: {current}/{total} ({percentage:.1f}%) | "
              f"Current: {symbol} | "
              f"Elapsed: {elapsed_time/60:.1f}m | "
              f"ETA: {remaining_time/60:.1f}m", end="", flush=True)
    else:
        print(f"\r📊 Starting collection for {symbol}...", end="", flush=True)


# Initialize start time for progress tracking
progress_callback.start_time = time.time()


def main():
    """Main data load process"""
    logger = setup_logging()
    
    print("🚀 S&P 500 Baseline Data Load")
    print("=" * 50)
    
    try:
        # Initialize managers
        logger.info("Initializing data collection components...")
        orchestrator = DataCollectionOrchestrator()
        universe_manager = StockUniverseManager()
        db_manager = DatabaseManager()
        db_ops = DatabaseOperationsManager(db_manager)
        
        # Connect to database
        db_manager.connect()
        db_manager.create_tables()
        
        print("✅ Database connection established")
        
        # Create backup before starting
        print("\n📦 Creating database backup...")
        backup_path = db_ops.create_backup(f"pre_sp500_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
        else:
            print("⚠️  Warning: Backup creation failed")
        
        # Update S&P 500 universe
        print("\n🔄 Updating S&P 500 universe...")
        if universe_manager.update_sp500_universe(force_refresh=True):
            print("✅ S&P 500 universe updated successfully")
            
            # Get universe info
            sp500_info = universe_manager.get_universe_info('sp500')
            stock_count = sp500_info['metadata']['stock_count']
            print(f"📈 Found {stock_count} S&P 500 stocks")
            
            # Show fetch metadata
            fetch_meta = sp500_info.get('fetch_metadata', {})
            print(f"📊 Source: {fetch_meta.get('source', 'Unknown')}")
            print(f"🕐 Fetch Date: {fetch_meta.get('fetch_date', 'Unknown')}")
            
        else:
            print("❌ Failed to update S&P 500 universe")
            return 1
        
        # Get collection time estimate
        print("\n⏱️  Estimating collection time...")
        status = orchestrator.get_universe_collection_status('sp500')
        time_estimate = status.get('estimated_time', {})
        
        total_hours = time_estimate.get('total_hours', 0)
        print(f"🕐 Estimated time: {total_hours:.1f} hours")
        print(f"   - Fundamentals: {time_estimate.get('breakdown', {}).get('fundamentals_minutes', 0):.1f} minutes")
        print(f"   - Prices: {time_estimate.get('breakdown', {}).get('prices_minutes', 0):.1f} minutes")
        print(f"   - News: {time_estimate.get('breakdown', {}).get('news_minutes', 0):.1f} minutes")
        print(f"   - Sentiment: {time_estimate.get('breakdown', {}).get('sentiment_minutes', 0):.1f} minutes")
        
        # Auto-proceed for baseline load
        print(f"\n🚀 Ready to collect data for {stock_count} S&P 500 stocks")
        print(f"   Estimated time: {total_hours:.1f} hours")
        print("   Proceeding automatically for baseline load...")
        
        # Start data collection
        print("\n🚀 Starting S&P 500 baseline data collection...")
        print("📝 Progress will be logged to file and console")
        
        progress_callback.start_time = time.time()
        
        # Collect data with progress tracking
        results = orchestrator.collect_sp500_baseline(progress_callback=progress_callback)
        
        print("\n")  # New line after progress bar
        
        # Display results
        if results.get('success'):
            print("✅ Data collection completed successfully!")
            
            stats = results.get('statistics', {})
            print(f"\n📊 Collection Statistics:")
            print(f"   ✅ Successful: {stats.get('successful', 0)}")
            print(f"   ❌ Failed: {stats.get('failed', 0)}")
            print(f"   📈 Success Rate: {(stats.get('successful', 0) / results.get('total_symbols', 1)) * 100:.1f}%")
            
            # Calculate actual time taken
            start_time = datetime.fromisoformat(results['start_time'])
            end_time = datetime.fromisoformat(results['end_time'])
            actual_duration = end_time - start_time
            
            print(f"   ⏱️  Actual Time: {actual_duration.total_seconds() / 3600:.1f} hours")
            
        else:
            print("❌ Data collection failed!")
            error = results.get('error', 'Unknown error')
            print(f"   Error: {error}")
            return 1
        
        # Database statistics
        print("\n📊 Database Statistics:")
        db_stats = db_manager.get_database_statistics()
        table_stats = db_stats.get('table_statistics', {})
        
        for table, stats in table_stats.items():
            count = stats.get('row_count', 0)
            print(f"   📁 {table}: {count:,} records")
        
        # Create post-collection backup
        print("\n📦 Creating post-collection backup...")
        final_backup = db_ops.create_backup(f"post_sp500_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if final_backup:
            print(f"✅ Final backup created: {final_backup}")
        
        # Export collection report
        print("\n📄 Generating collection report...")
        report_path = f"data/sp500_collection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            import json
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✅ Report saved: {report_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save report: {e}")
        
        print("\n🎉 S&P 500 baseline data load completed successfully!")
        print("   You can now use the dashboard to explore the data.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n❌ Data collection interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        print(f"\n❌ Data collection failed: {e}")
        return 1
        
    finally:
        # Cleanup
        try:
            db_manager.close()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())