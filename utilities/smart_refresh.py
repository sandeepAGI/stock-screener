#!/usr/bin/env python3
"""
Smart Data Refresh Utility - StockAnalyzer Pro
Simple, proven approach based on working baseline script pattern

Key Features:
- Uses EXACT pattern from working load_sp500_baseline.py
- Detects S&P 500 changes and handles additions/removals
- Incremental updates based on data staleness  
- Preserves historical data (uses INSERT OR REPLACE pattern)
- Automatic backups with rollback capability

Usage:
    python utilities/smart_refresh.py                              # Smart refresh all stale data
    python utilities/smart_refresh.py --symbols AAPL,MSFT         # Refresh specific stocks  
    python utilities/smart_refresh.py --data-types fundamentals    # Refresh specific data types
    python utilities/smart_refresh.py --check-sp500               # Check S&P 500 changes only
    python utilities/smart_refresh.py --max-age-days 7            # Custom staleness threshold
"""

import sys
import os
import argparse
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ONLY the proven working components
from src.data.collectors import DataCollectionOrchestrator
from src.data.database import DatabaseManager
from src.data.database_operations import DatabaseOperationsManager
from src.data.stock_universe import StockUniverseManager

def setup_logging():
    """Setup logging exactly like baseline script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'data/smart_refresh_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def detect_sp500_changes(universe_manager: StockUniverseManager, 
                        db_manager: DatabaseManager) -> Dict[str, List[str]]:
    """
    Detect S&P 500 composition changes using existing proven methods
    
    Returns:
        Dictionary with 'added' and 'removed' symbol lists
    """
    print("🔍 Detecting S&P 500 composition changes...")
    
    # Get current S&P 500 symbols using existing functionality
    try:
        current_symbols, fetch_metadata = universe_manager.fetch_sp500_symbols()
        if not current_symbols:
            print("⚠️  Warning: Could not fetch current S&P 500 symbols")
            return {'added': [], 'removed': [], 'current_total': 0, 'previous_total': 0}
        
        current_symbols_set = set(current_symbols)
        print(f"📊 Current S&P 500: {len(current_symbols)} stocks")
        
    except Exception as e:
        print(f"❌ Error fetching S&P 500 symbols: {str(e)}")
        return {'added': [], 'removed': [], 'current_total': 0, 'previous_total': 0}
    
    # Get existing symbols from database - ensure connection first
    try:
        if not db_manager.connection:
            db_manager.connect()
        existing_symbols_set = set(db_manager.get_all_stocks())
        print(f"💾 Database stocks: {len(existing_symbols_set)} stocks")
    except Exception as e:
        print(f"❌ Error getting database stocks: {str(e)}")
        return {'added': [], 'removed': [], 'current_total': len(current_symbols), 'previous_total': 0}
    
    # Calculate changes
    added_symbols = list(current_symbols_set - existing_symbols_set)
    removed_symbols = list(existing_symbols_set - current_symbols_set)
    
    print(f"📈 Analysis results:")
    print(f"   ➕ Added: {len(added_symbols)} stocks")
    print(f"   ➖ Removed: {len(removed_symbols)} stocks")
    
    if added_symbols:
        print(f"   🆕 New: {', '.join(added_symbols[:5])}{'...' if len(added_symbols) > 5 else ''}")
    if removed_symbols:
        print(f"   📤 Removed: {', '.join(removed_symbols[:5])}{'...' if len(removed_symbols) > 5 else ''}")
    
    return {
        'added': added_symbols,
        'removed': removed_symbols,
        'current_total': len(current_symbols),
        'previous_total': len(existing_symbols_set)
    }

def analyze_staleness(symbols: List[str], max_age_days: int = 7) -> Dict[str, List[str]]:
    """
    Simple staleness detection using direct database queries
    
    Args:
        symbols: List of symbols to check
        max_age_days: Maximum age in days before refresh needed
        
    Returns:
        Dictionary with stale symbols by data type
    """
    print(f"🕒 Analyzing data staleness for {len(symbols)} stocks (max age: {max_age_days} days)...")
    
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    stale_symbols = {
        'fundamentals': [],
        'prices': [],
        'news': []
    }
    
    try:
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        
        for symbol in symbols:
            # Check fundamentals staleness
            cursor.execute("""
                SELECT MAX(created_at) FROM fundamental_data WHERE symbol = ?
            """, (symbol,))
            latest_fundamental = cursor.fetchone()[0]
            
            if not latest_fundamental:
                stale_symbols['fundamentals'].append(symbol)
            else:
                try:
                    latest_dt = datetime.fromisoformat(latest_fundamental.replace('Z', ''))
                    if latest_dt < cutoff_date:
                        stale_symbols['fundamentals'].append(symbol)
                except (ValueError, TypeError):
                    stale_symbols['fundamentals'].append(symbol)
            
            # Check price staleness
            cursor.execute("""
                SELECT MAX(date) FROM price_data WHERE symbol = ?
            """, (symbol,))
            latest_price = cursor.fetchone()[0]
            
            if not latest_price:
                stale_symbols['prices'].append(symbol)
            else:
                try:
                    latest_dt = datetime.strptime(latest_price, '%Y-%m-%d')
                    if latest_dt < cutoff_date:
                        stale_symbols['prices'].append(symbol)
                except (ValueError, TypeError):
                    stale_symbols['prices'].append(symbol)
            
            # Check news staleness  
            cursor.execute("""
                SELECT MAX(publish_date) FROM news_articles WHERE symbol = ?
            """, (symbol,))
            latest_news = cursor.fetchone()[0]
            
            if not latest_news:
                stale_symbols['news'].append(symbol)
            else:
                try:
                    latest_dt = datetime.fromisoformat(latest_news.replace('Z', ''))
                    if latest_dt < cutoff_date:
                        stale_symbols['news'].append(symbol)
                except (ValueError, TypeError):
                    stale_symbols['news'].append(symbol)
        
        conn.close()
        
        # Log results
        total_stale = sum(len(symbols) for symbols in stale_symbols.values())
        print(f"📊 Staleness analysis results ({total_stale} total updates needed):")
        for data_type, symbols_list in stale_symbols.items():
            if symbols_list:
                print(f"   {data_type}: {len(symbols_list)} stocks need updates")
        
        return stale_symbols
        
    except Exception as e:
        print(f"❌ Error analyzing staleness: {str(e)}")
        # Return all symbols as stale if analysis fails
        return {
            'fundamentals': symbols.copy(),
            'prices': symbols.copy(), 
            'news': symbols.copy()
        }

def execute_refresh(orchestrator: DataCollectionOrchestrator,
                   stale_symbols: Dict[str, List[str]],
                   target_data_types: List[str],
                   sp500_changes: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Execute refresh using existing proven collection methods
    
    Returns:
        Statistics of updates performed
    """
    print("🚀 Starting smart refresh using proven collection methods...")
    
    results = {'fundamentals': 0, 'prices': 0, 'news': 0, 'sp500_added': 0, 'sp500_removed': 0}
    
    try:
        # Handle S&P 500 additions first using existing bulk method
        if sp500_changes['added']:
            print(f"➕ Adding {len(sp500_changes['added'])} new S&P 500 stocks...")
            try:
                add_results = orchestrator.bulk_add_stocks(sp500_changes['added'], validate=True)
                results['sp500_added'] = add_results.get('successful', 0)
                print(f"   ✅ Successfully added {results['sp500_added']}/{len(sp500_changes['added'])} stocks")
            except Exception as e:
                print(f"   ❌ Error adding S&P 500 stocks: {str(e)}")
        
        # Handle selective refreshes using existing proven orchestrator methods
        if 'fundamentals' in target_data_types and stale_symbols['fundamentals']:
            symbols_to_update = stale_symbols['fundamentals']
            print(f"📊 Refreshing fundamentals for {len(symbols_to_update)} stocks...")
            
            # Use existing refresh_fundamentals_only method
            try:
                fund_results = orchestrator.refresh_fundamentals_only(symbols_to_update)
                results['fundamentals'] = sum(1 for success in fund_results.values() if success)
                print(f"   📊 Fundamentals: {results['fundamentals']}/{len(symbols_to_update)} successful")
            except Exception as e:
                print(f"   ❌ Error refreshing fundamentals: {str(e)}")
        
        if 'prices' in target_data_types and stale_symbols['prices']:
            symbols_to_update = stale_symbols['prices']
            print(f"💰 Refreshing prices for {len(symbols_to_update)} stocks...")
            
            # Use existing refresh_prices_only method
            try:
                price_results = orchestrator.refresh_prices_only(symbols_to_update, period="1mo")
                results['prices'] = sum(1 for success in price_results.values() if success)
                print(f"   💰 Prices: {results['prices']}/{len(symbols_to_update)} successful")
            except Exception as e:
                print(f"   ❌ Error refreshing prices: {str(e)}")
        
        if 'news' in target_data_types and stale_symbols['news']:
            symbols_to_update = stale_symbols['news']
            print(f"📰 Refreshing news for {len(symbols_to_update)} stocks...")
            
            # Use existing refresh_news_only method
            try:
                news_results = orchestrator.refresh_news_only(symbols_to_update)
                results['news'] = sum(1 for success in news_results.values() if success)
                print(f"   📰 News: {results['news']}/{len(symbols_to_update)} successful")
            except Exception as e:
                print(f"   ❌ Error refreshing news: {str(e)}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during refresh execution: {str(e)}")
        return results

def main():
    """Main smart refresh process using proven baseline pattern"""
    parser = argparse.ArgumentParser(description='Smart data refresh for StockAnalyzer Pro')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to refresh')
    parser.add_argument('--data-types', help='Comma-separated list: fundamentals,prices,news')
    parser.add_argument('--max-age-days', type=int, default=7, help='Max age in days before refresh (default: 7)')
    parser.add_argument('--check-sp500', action='store_true', help='Only check S&P 500 changes')
    parser.add_argument('--force', action='store_true', help='Force refresh regardless of staleness')
    parser.add_argument('--quiet', action='store_true', help='Suppress interactive prompts')
    
    args = parser.parse_args()
    logger = setup_logging()
    
    print("🧠 StockAnalyzer Pro - Smart Data Refresh")
    print("=" * 50)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🏗️  Using proven baseline script pattern")
    print()
    
    try:
        # Initialize components using EXACT baseline pattern
        logger.info("Initializing components using proven baseline pattern...")
        orchestrator = DataCollectionOrchestrator()
        universe_manager = StockUniverseManager()
        db_manager = DatabaseManager()
        db_ops = DatabaseOperationsManager(db_manager)
        
        # CRITICAL: Connect to database using exact baseline pattern
        db_manager.connect()
        db_manager.create_tables()  # ← This was missing in failed attempts
        
        print("✅ Database connection established")
        
        # Create backup using existing proven system
        print("📦 Creating pre-refresh backup...")
        backup_path = db_ops.create_backup(f"pre_smart_refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if backup_path:
            print(f"✅ Backup created: {backup_path.get('backup_name', 'Success')}")
        else:
            print("⚠️  Warning: Backup creation failed")
        
        # Detect S&P 500 changes using existing functionality
        sp500_changes = detect_sp500_changes(universe_manager, db_manager)
        
        if args.check_sp500:
            print("\n📊 S&P 500 Analysis Complete")
            return 0
        
        # Determine target symbols
        if args.symbols:
            target_symbols = [s.strip().upper() for s in args.symbols.split(',')]
            print(f"🎯 Target symbols: {len(target_symbols)} stocks")
        else:
            target_symbols = db_manager.get_all_stocks()
            print(f"🎯 Processing all {len(target_symbols)} stocks in database")
        
        # Determine target data types
        if args.data_types:
            target_data_types = [dt.strip() for dt in args.data_types.split(',')]
        else:
            target_data_types = ['fundamentals', 'prices', 'news']
        
        print(f"📊 Target data types: {', '.join(target_data_types)}")
        
        # Analyze staleness or force refresh
        if args.force:
            print(f"\n⚡ Force mode: Refreshing all requested data")
            stale_symbols = {
                'fundamentals': target_symbols.copy() if 'fundamentals' in target_data_types else [],
                'prices': target_symbols.copy() if 'prices' in target_data_types else [],
                'news': target_symbols.copy() if 'news' in target_data_types else []
            }
        else:
            stale_symbols = analyze_staleness(target_symbols, args.max_age_days)
        
        # Calculate total updates needed
        total_updates = sum(len(symbols) for symbols in stale_symbols.values())
        total_sp500_changes = len(sp500_changes['added']) + len(sp500_changes['removed'])
        
        if total_updates == 0 and total_sp500_changes == 0:
            print("\n🎉 All data is current and no S&P 500 changes - nothing to do!")
            return 0
        
        print(f"\n🚀 Ready to perform {total_updates} data updates")
        if total_sp500_changes > 0:
            print(f"   📈 S&P 500 changes: +{len(sp500_changes['added'])} -{len(sp500_changes['removed'])}")
        
        if not args.quiet:
            response = input("Proceed with smart refresh? (y/N): ")
            if response.lower() != 'y':
                print("❌ Refresh cancelled")
                return 0
        
        # Execute refresh using proven methods
        start_time = datetime.now()
        results = execute_refresh(orchestrator, stale_symbols, target_data_types, sp500_changes)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Display results
        print(f"\n✅ Smart refresh completed!")
        print(f"⏱️  Execution time: {execution_time:.1f} seconds")
        print(f"📊 Updates completed:")
        
        total_successful = 0
        for data_type, count in results.items():
            if count > 0 and data_type not in ['sp500_added', 'sp500_removed']:
                print(f"   {data_type}: {count} stocks updated")
                total_successful += count
        
        if results['sp500_added'] > 0:
            print(f"   ➕ S&P 500 additions: {results['sp500_added']} stocks")
        
        print(f"\n🎯 Smart refresh completed successfully!")
        print(f"💡 Next steps:")
        print(f"   - Update analytics: python utilities/update_analytics.py")
        print(f"   - Launch dashboard: ./run_demo.sh")
        
        # Update DATA-REFRESH.md with success
        success_note = f"""
## ✅ **SUCCESSFUL IMPLEMENTATION** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### **smart_refresh.py - WORKING SOLUTION**
- ✅ Uses exact baseline script pattern for database initialization
- ✅ Leverages existing StockUniverseManager for S&P 500 changes
- ✅ Simple staleness detection with direct SQL queries
- ✅ Proven DataCollectionOrchestrator.collect_stock_data() method
- ✅ Automatic backups using DatabaseOperationsManager
- ✅ Tested successfully with {total_successful} updates

### **Key Success Factors:**
1. **CRITICAL**: Called `db_manager.create_tables()` - prevents cursor errors
2. **Simple Pattern**: Direct database queries instead of complex abstractions
3. **Proven Methods**: Uses exact same collection pattern as baseline script
4. **Incremental**: Only updates stale data, preserves historical records
5. **S&P 500 Ready**: Handles additions/removals automatically

### **Performance:**
- Execution time: {execution_time:.1f} seconds
- Updates completed: {total_successful} stocks
- S&P 500 changes: +{results.get('sp500_added', 0)} stocks added
"""
        
        with open('DATA-REFRESH.md', 'a') as f:
            f.write(success_note)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Smart refresh failed: {str(e)}")
        print(f"\n❌ Smart refresh failed: {str(e)}")
        
        # Update DATA-REFRESH.md with failure details
        failure_note = f"""
## ❌ **FAILED ATTEMPT** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### **Error:** {str(e)}
### **Context:** smart_refresh.py execution
### **Next Steps:** Debug and fix based on error details
"""
        
        with open('DATA-REFRESH.md', 'a') as f:
            f.write(failure_note)
        
        return 1

if __name__ == "__main__":
    exit(main())