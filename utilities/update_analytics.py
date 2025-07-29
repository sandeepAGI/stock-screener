#!/usr/bin/env python3
"""
Analytics Update Utility - StockAnalyzer Pro
Recalculate composite scores and analytics after data updates

Usage:
    python utilities/update_analytics.py                         # Update analytics for all stocks
    python utilities/update_analytics.py --symbols AAPL,MSFT    # Update specific stocks
    python utilities/update_analytics.py --force-recalculate    # Force recalculation even if recent
    python utilities/update_analytics.py --batch-size 50        # Custom batch processing size
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

# Add project root to path  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.calculations.composite import CompositeCalculator
from src.calculations.fundamental import FundamentalCalculator
from src.calculations.quality import QualityCalculator
from src.calculations.growth import GrowthCalculator
from src.calculations.sentiment import SentimentCalculator
from src.data.database import DatabaseManager
from src.analysis.data_quality import QualityAnalyticsEngine

def setup_logging():
    """Setup logging for analytics update operations"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'data/analytics_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_stocks_needing_update(db: DatabaseManager, symbols: Optional[List[str]] = None, 
                            force_recalculate: bool = False, 
                            max_age_hours: int = 24) -> Tuple[List[str], Dict[str, datetime]]:
    """
    Determine which stocks need analytics updates
    
    Args:
        db: Database manager instance
        symbols: Specific symbols to check (None = all stocks)  
        force_recalculate: Force update regardless of age
        max_age_hours: Maximum age in hours before update needed
        
    Returns:
        Tuple of (stocks_needing_update, last_calculation_times)
    """
    cursor = db.connection.cursor()
    
    # Get target stocks
    if symbols:
        target_stocks = [s.upper() for s in symbols if s.upper() in db.get_all_stocks()]
    else:
        target_stocks = db.get_all_stocks()
    
    stocks_needing_update = []
    last_calc_times = {}
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    for symbol in target_stocks:
        # Get latest calculation timestamp
        cursor.execute('''
            SELECT created_at FROM calculated_metrics 
            WHERE symbol = ? 
            ORDER BY created_at DESC LIMIT 1
        ''', (symbol,))
        
        result = cursor.fetchone()
        
        if not result or force_recalculate:
            # No calculation exists or forced recalculation
            stocks_needing_update.append(symbol)
            last_calc_times[symbol] = None
            continue
            
        calc_timestamp = result[0]
        if isinstance(calc_timestamp, str):
            calc_timestamp = datetime.fromisoformat(calc_timestamp.replace('T', ' '))
        
        last_calc_times[symbol] = calc_timestamp
        
        # Check if data has been updated since last calculation
        needs_update = False
        for table_name in ['fundamental_data', 'price_data', 'news_articles']:
            cursor.execute(f'''
                SELECT MAX(created_at) FROM {table_name} 
                WHERE symbol = ?
            ''', (symbol,))
            
            data_result = cursor.fetchone()
            if data_result and data_result[0]:
                data_timestamp = data_result[0]
                if isinstance(data_timestamp, str):
                    if 'T' in data_timestamp:
                        data_timestamp = datetime.fromisoformat(data_timestamp)
                    else:
                        data_timestamp = datetime.strptime(data_timestamp, '%Y-%m-%d %H:%M:%S')
                
                # If any data is newer than calculation, need to recalculate
                if data_timestamp > calc_timestamp:
                    needs_update = True
                    break
        
        # Also check if calculation is older than cutoff
        if calc_timestamp < cutoff_time:
            needs_update = True
        
        if needs_update:
            stocks_needing_update.append(symbol)
    
    cursor.close()
    return stocks_needing_update, last_calc_times

def calculate_analytics_batch(symbols: List[str], calculators: Dict, 
                            db: DatabaseManager, logger: logging.Logger) -> Dict[str, bool]:
    """
    Calculate analytics for a batch of symbols
    
    Args:
        symbols: List of symbols to process
        calculators: Dictionary of calculator instances
        db: Database manager
        logger: Logger instance
        
    Returns:
        Dict mapping symbol to success status
    """
    results = {}
    composite_calc = calculators['composite']
    
    logger.info(f"🔄 Processing batch: {', '.join(symbols)}")
    
    try:
        # Use batch calculation for efficiency
        batch_results = composite_calc.calculate_batch_composite(symbols, db)
        
        # Save results
        if batch_results:
            composite_calc.save_composite_scores(batch_results, db)
            
            for symbol in symbols:
                if symbol in batch_results:
                    results[symbol] = True
                    logger.info(f"✅ {symbol}: Analytics updated successfully")
                else:
                    results[symbol] = False
                    logger.warning(f"⚠️  {symbol}: Analytics calculation failed")
        else:
            for symbol in symbols:
                results[symbol] = False
                logger.error(f"❌ {symbol}: Batch calculation failed")
    
    except Exception as e:
        logger.error(f"❌ Batch calculation error: {str(e)}")
        for symbol in symbols:
            results[symbol] = False
    
    return results

def update_analytics(symbols: Optional[List[str]] = None,
                    force_recalculate: bool = False,
                    batch_size: int = 25,
                    logger: logging.Logger = None) -> bool:
    """
    Update analytics for specified stocks
    
    Args:
        symbols: List of stock symbols to update (None = all stocks)
        force_recalculate: Force recalculation regardless of age
        batch_size: Number of stocks to process per batch
        logger: Logger instance
        
    Returns:
        bool: Overall success status
    """
    try:
        logger.info("📊 Starting Analytics Update Utility")
        logger.info("=" * 50)
        
        # Initialize components
        db = DatabaseManager()
        if not db.connect():
            logger.error("❌ Failed to connect to database")
            return False
        
        # Initialize calculators
        calculators = {
            'fundamental': FundamentalCalculator(),
            'quality': QualityCalculator(), 
            'growth': GrowthCalculator(),
            'sentiment': SentimentCalculator(),
            'composite': CompositeCalculator()
        }
        
        quality_engine = QualityAnalyticsEngine()
        
        # Determine stocks needing update
        stocks_to_update, last_calc_times = get_stocks_needing_update(
            db, symbols, force_recalculate
        )
        
        if not stocks_to_update:
            logger.info("✅ All analytics are up to date - no updates needed")
            return True
        
        logger.info(f"🎯 Found {len(stocks_to_update)} stocks needing analytics updates")
        logger.info(f"📊 Stocks to process: {', '.join(stocks_to_update)}")
        
        # Process in batches
        total_processed = 0
        total_success = 0
        start_time = datetime.now()
        
        for i in range(0, len(stocks_to_update), batch_size):
            batch = stocks_to_update[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(stocks_to_update) + batch_size - 1) // batch_size
            
            logger.info(f"🔄 Processing batch {batch_num}/{total_batches}")
            
            # Calculate analytics for this batch
            batch_results = calculate_analytics_batch(batch, calculators, db, logger)
            
            # Update counters
            for symbol, success in batch_results.items():
                total_processed += 1
                if success:
                    total_success += 1
            
            # Progress update
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining_stocks = len(stocks_to_update) - total_processed
            if total_processed > 0:
                eta_seconds = (elapsed / total_processed) * remaining_stocks
                logger.info(f"📈 Progress: {total_processed}/{len(stocks_to_update)} "
                           f"({total_success} successful) | ETA: {eta_seconds/60:.1f}m")
        
        # Final summary
        elapsed_time = (datetime.now() - start_time).total_seconds()
        success_rate = (total_success / total_processed) * 100 if total_processed > 0 else 0
        
        logger.info("=" * 50) 
        logger.info("📊 Analytics Update Summary")
        logger.info(f"✅ Successfully updated: {total_success}/{total_processed} stocks")
        logger.info(f"📈 Success rate: {success_rate:.1f}%")
        logger.info(f"⏱️  Total time: {elapsed_time:.1f} seconds")
        logger.info(f"⚡ Processing rate: {total_processed/elapsed_time:.1f} stocks/second")
        
        # Run quality analysis on updated data
        logger.info("🔍 Running data quality analysis...")
        try:
            quality_report = quality_engine.generate_comprehensive_quality_report()
            overall_quality = quality_report.overall_quality_score
            logger.info(f"📊 Overall data quality: {overall_quality*100:.1f}%")
            
            if overall_quality > 0.8:
                logger.info("✅ Data quality analysis passed - high quality analytics")
            else:
                logger.warning("⚠️  Data quality concerns detected - review analytics carefully")
                
        except Exception as e:
            logger.warning(f"⚠️  Quality analysis failed: {str(e)}")
        
        # Determine overall success
        if success_rate >= 90:
            logger.info("✅ Analytics update completed successfully!")
            return True
        elif success_rate >= 70:
            logger.warning("⚠️  Analytics update completed with some failures")
            return True
        else:
            logger.error("❌ Analytics update failed - too many calculation failures")
            return False
        
    except Exception as e:
        logger.error(f"❌ Analytics update utility failed: {str(e)}")
        return False
    
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Update analytics for StockAnalyzer Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python utilities/update_analytics.py                         # Update analytics for all stocks
  python utilities/update_analytics.py --symbols AAPL,MSFT    # Update specific stocks
  python utilities/update_analytics.py --force-recalculate    # Force recalculation even if recent
  python utilities/update_analytics.py --batch-size 50        # Custom batch processing size
        """
    )
    
    parser.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated list of stock symbols to update (e.g., AAPL,MSFT,GOOGL)'
    )
    
    parser.add_argument(
        '--force-recalculate',
        action='store_true',
        help='Force recalculation even if analytics are recent'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=25,
        help='Number of stocks to process per batch (default: 25)'
    )
    
    parser.add_argument(
        '--max-age-hours',
        type=int,
        default=24,
        help='Maximum age in hours before update needed (default: 24)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress interactive prompts'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
    
    # Show summary
    print("📊 StockAnalyzer Pro - Analytics Update Utility")
    print("=" * 50)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if symbols:
        print(f"🎯 Target Stocks: {', '.join(symbols)} ({len(symbols)} stocks)")
    else:
        print("🎯 Target Stocks: All stocks in database")
    
    print(f"🔄 Force Recalculate: {'Yes' if args.force_recalculate else 'No'}")
    print(f"📦 Batch Size: {args.batch_size} stocks per batch")
    print(f"⏰ Max Age: {args.max_age_hours} hours")
    print()
    
    # Confirm before proceeding (unless quiet mode)
    if not args.quiet:
        response = input("Proceed with analytics update? (Y/n): ")
        if response.lower() == 'n':
            print("❌ Analytics update cancelled by user")
            return
    
    # Execute update
    success = update_analytics(
        symbols=symbols,
        force_recalculate=args.force_recalculate,
        batch_size=args.batch_size,
        logger=logger
    )
    
    if success:
        print("\n✅ Analytics update completed successfully!")
        print("💡 Next steps:")
        print("   - Launch dashboard: ./run_demo.sh")
        print("   - View analytics: http://localhost:8503")
    else:
        print("\n❌ Analytics update failed - check logs for details")
        sys.exit(1)

if __name__ == "__main__":
    main()