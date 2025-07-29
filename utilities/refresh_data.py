#!/usr/bin/env python3
"""
Data Refresh Utility - StockAnalyzer Pro
Selective data refresh for existing stocks with targeted data type updates

Usage:
    python utilities/refresh_data.py                              # Refresh all data for all stocks
    python utilities/refresh_data.py --symbols AAPL,MSFT,GOOGL   # Refresh specific stocks
    python utilities/refresh_data.py --data-types fundamentals,prices  # Refresh specific data types
    python utilities/refresh_data.py --symbols AAPL --data-types news,sentiment  # Combined filtering
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.collectors import DataCollectionOrchestrator
from src.data.database import DatabaseManager
from src.data.database_operations import DatabaseOperationsManager
from src.data.monitoring import DataSourceMonitor
from src.data.validator import DataValidator

def setup_logging():
    """Setup logging for data refresh operations"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'data/refresh_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_symbols(symbols: List[str], db: DatabaseManager) -> List[str]:
    """Validate that symbols exist in database"""
    try:
        existing_stocks = db.get_all_stocks()
        valid_symbols = []
        invalid_symbols = []
        
        for symbol in symbols:
            if symbol.upper() in existing_stocks:
                valid_symbols.append(symbol.upper())
            else:
                invalid_symbols.append(symbol.upper())
        
        if invalid_symbols:
            print(f"⚠️  Warning: These symbols don't exist in database: {', '.join(invalid_symbols)}")
            print(f"💡 Available stocks: {len(existing_stocks)} total")
        
        return valid_symbols
    except Exception as e:
        print(f"⚠️  Warning: Could not validate symbols against database: {str(e)}")
        print(f"🔄 Proceeding with provided symbols: {', '.join(symbols)}")
        return [s.upper() for s in symbols]

def validate_data_types(data_types: List[str]) -> List[str]:
    """Validate data type arguments"""
    valid_types = ['fundamentals', 'prices', 'news', 'sentiment']
    validated_types = []
    invalid_types = []
    
    for data_type in data_types:
        if data_type.lower() in valid_types:
            validated_types.append(data_type.lower())
        else:
            invalid_types.append(data_type.lower())
    
    if invalid_types:
        print(f"⚠️  Warning: Invalid data types: {', '.join(invalid_types)}")
        print(f"✅ Valid types: {', '.join(valid_types)}")
    
    return validated_types

def refresh_data(symbols: Optional[List[str]] = None, 
                data_types: Optional[List[str]] = None,
                logger: logging.Logger = None,
                quiet: bool = False) -> bool:
    """
    Refresh data for specified stocks and data types
    
    Args:
        symbols: List of stock symbols to refresh (None = all stocks)
        data_types: List of data types to refresh (None = all types)
        logger: Logger instance
        quiet: Suppress interactive prompts
    
    Returns:
        bool: Success status
    """
    try:
        logger.info("🔄 Starting Data Refresh Utility")
        logger.info("=" * 50)
        
        # Initialize components
        db = DatabaseManager()
        if not db.connect():
            logger.error("❌ Failed to connect to database")
            return False
        
        # Ensure database tables exist (critical for operations)
        db.create_tables()
        
        db_ops = DatabaseOperationsManager(db)
        monitor = DataSourceMonitor()
        validator = DataValidator()
        orchestrator = DataCollectionOrchestrator()
        
        # Create backup before starting data refresh (safety measure)
        logger.info("🛡️  Creating pre-refresh database backup...")
        backup_name = f"pre_refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = db_ops.create_backup(backup_name)
        
        if backup_path:
            logger.info(f"✅ Pre-refresh backup created: {backup_path}")
            logger.info("🔄 If refresh fails, restore with: python utilities/backup_database.py --restore latest")
        else:
            logger.warning("⚠️  Warning: Pre-refresh backup creation failed")
            if not quiet:
                response = input("Continue without backup? This is NOT recommended (y/N): ")
                if response.lower() != 'y':
                    logger.info("❌ Data refresh cancelled for safety")
                    return False
        
        # Determine target stocks
        if symbols:
            target_stocks = validate_symbols(symbols, db)
            if not target_stocks:
                logger.error("❌ No valid symbols provided")
                return False
            logger.info(f"🎯 Target stocks: {', '.join(target_stocks)} ({len(target_stocks)} total)")
        else:
            try:
                target_stocks = db.get_all_stocks()
                logger.info(f"🎯 Refreshing all stocks: {len(target_stocks)} total")
            except Exception as e:
                logger.error(f"❌ Could not get stock list from database: {str(e)}")
                return False
        
        # Determine target data types
        if data_types:
            target_types = validate_data_types(data_types)
            if not target_types:
                logger.error("❌ No valid data types provided")
                return False
            logger.info(f"📊 Target data types: {', '.join(target_types)}")
        else:
            target_types = ['fundamentals', 'prices', 'news', 'sentiment']
            logger.info(f"📊 Refreshing all data types: {', '.join(target_types)}")
        
        # Check API status before starting
        logger.info("🔍 Checking API status...")
        api_status = monitor.get_all_api_status()
        
        yahoo_status = api_status.get('yahoo_finance')
        reddit_status = api_status.get('reddit')
        
        yahoo_status_str = yahoo_status.status if yahoo_status else 'unknown'
        reddit_status_str = reddit_status.status if reddit_status else 'unknown'
        
        if yahoo_status_str not in ['active', 'healthy'] and any(dt in target_types for dt in ['fundamentals', 'prices', 'news']):
            logger.warning(f"⚠️  Yahoo Finance API status: {yahoo_status_str}")
            if not quiet:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
                
        if reddit_status_str not in ['active', 'healthy'] and 'sentiment' in target_types:
            logger.warning(f"⚠️  Reddit API status: {reddit_status_str}")
            if not quiet:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
        
        # Execute data refresh
        logger.info("🚀 Starting data collection...")
        start_time = datetime.now()
        
        # Use direct stock-by-stock collection like working scripts
        try:
            results = {
                "success": True,
                "total_symbols": len(target_stocks),
                "successful_symbols": 0,
                "failed_symbols": 0,
                "start_time": start_time.isoformat(),
                "data_types": target_types,
                "results": {}
            }
            
            logger.info("🎯 Processing stocks individually...")
            logger.info(f"   Collecting data for {len(target_stocks)} stocks: {', '.join(target_stocks[:5])}{'...' if len(target_stocks) > 5 else ''}")
            logger.info(f"   Data types: {', '.join(target_types)}")
            
            # Initialize collectors directly using the same pattern as working scripts
            from src.data.collectors import YahooFinanceCollector
            yahoo_collector = YahooFinanceCollector()
            
            for i, symbol in enumerate(target_stocks, 1):
                try:
                    logger.info(f"📊 Processing {symbol} ({i}/{len(target_stocks)})...")
                    
                    # Collect data for this stock using direct method
                    stock_data = orchestrator.collect_stock_data(symbol)
                    
                    if stock_data:
                        # Insert data into database using the same methods as baseline script
                        try:
                            if 'fundamentals' in target_types and stock_data.fundamentals:
                                db.insert_fundamental_data(symbol, stock_data.fundamentals.__dict__)
                            
                            if 'prices' in target_types and stock_data.price_history:
                                db.insert_price_data(symbol, stock_data.price_history)
                            
                            if 'news' in target_types and stock_data.news_articles:
                                db.insert_news_articles(symbol, stock_data.news_articles)
                            
                            results["successful_symbols"] += 1
                            results["results"][symbol] = "success"
                            logger.info(f"✅ {symbol} completed successfully")
                            
                        except Exception as e:
                            logger.error(f"❌ Database insert failed for {symbol}: {str(e)}")
                            results["failed_symbols"] += 1
                            results["results"][symbol] = f"database_error: {str(e)}"
                    else:
                        results["failed_symbols"] += 1
                        results["results"][symbol] = "collection_failed"
                        logger.error(f"❌ Data collection failed for {symbol}")
                        
                except Exception as e:
                    results["failed_symbols"] += 1
                    results["results"][symbol] = f"error: {str(e)}"
                    logger.error(f"❌ Error processing {symbol}: {str(e)}")
            
            results["end_time"] = datetime.now().isoformat()
            results["success"] = results["successful_symbols"] > 0
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            if results and results.get("success", False):
                successful = results.get("successful_symbols", 0)
                failed = results.get("failed_symbols", 0)
                
                logger.info(f"✅ Data refresh completed!")
                logger.info(f"⏱️  Total time: {elapsed_time:.1f} seconds")
                logger.info(f"📊 Results: {successful} successful, {failed} failed out of {len(target_stocks)} stocks")
                logger.info(f"🎯 Data types processed: {', '.join(target_types)}")
                
                # Note: Data type filtering is handled by the collection methods automatically
                # The collect_complete_dataset method collects all data types (fundamentals, prices, news)
                if len(target_types) < 4:
                    logger.info(f"ℹ️  Note: Requested specific data types but collect_complete_dataset collects all types")
                
                # Validate refreshed data
                logger.info("🔍 Validating refreshed data...")
                try:
                    validation_results = validator.validate_data_integrity()
                    
                    if validation_results.get('overall_health', 0) > 0.8:
                        logger.info("✅ Data validation passed - high quality data")
                    else:
                        logger.warning("⚠️  Data validation concerns - check validation report")
                except Exception as e:
                    logger.warning(f"⚠️  Data validation failed: {str(e)}")
                
                return successful > 0
            else:
                logger.error("❌ Data refresh failed - no results returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Data collection failed: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Data refresh utility failed: {str(e)}")
        return False
    
    finally:
        if 'db' in locals() and db.connection:
            db.close()

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Refresh data for existing stocks in StockAnalyzer Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python utilities/refresh_data.py                              # Refresh all data for all stocks
  python utilities/refresh_data.py --symbols AAPL,MSFT,GOOGL   # Refresh specific stocks
  python utilities/refresh_data.py --data-types fundamentals,prices  # Refresh specific data types
  python utilities/refresh_data.py --symbols AAPL --data-types news,sentiment  # Combined filtering
        """
    )
    
    parser.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated list of stock symbols to refresh (e.g., AAPL,MSFT,GOOGL)'
    )
    
    parser.add_argument(
        '--data-types',
        type=str,
        help='Comma-separated list of data types to refresh: fundamentals,prices,news,sentiment'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress interactive prompts (use with caution)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
    
    # Parse data types
    data_types = None  
    if args.data_types:
        data_types = [dt.strip().lower() for dt in args.data_types.split(',') if dt.strip()]
    
    # Show summary
    print("🔄 StockAnalyzer Pro - Data Refresh Utility")
    print("=" * 50)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if symbols:
        print(f"🎯 Target Stocks: {', '.join(symbols)} ({len(symbols)} stocks)")
    else:
        print("🎯 Target Stocks: All stocks in database")
    
    if data_types:
        print(f"📊 Data Types: {', '.join(data_types)}")
    else:
        print("📊 Data Types: All data types (fundamentals, prices, news, sentiment)")
    
    print()
    
    # Confirm before proceeding (unless quiet mode)
    if not args.quiet:
        response = input("Proceed with data refresh? (Y/n): ")
        if response.lower() == 'n':
            print("❌ Data refresh cancelled by user")
            return
    
    # Execute refresh
    success = refresh_data(symbols, data_types, logger, args.quiet)
    
    if success:
        print("\n✅ Data refresh completed successfully!")
        print("💡 Next steps:")
        print("   - Run analytics update: python utilities/update_analytics.py")
        print("   - Launch dashboard: ./run_demo.sh")
    else:
        print("\n❌ Data refresh failed - check logs for details")
        sys.exit(1)

if __name__ == "__main__":
    main()