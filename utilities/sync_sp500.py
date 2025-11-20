#!/usr/bin/env python3
"""
S&P 500 Universe Sync Utility

Fetches current S&P 500 composition and syncs with database.
- Marks removed stocks as inactive (is_active=0)
- Adds new stocks with full data collection
- Preserves historical data for removed stocks

Usage:
    # Check for changes only (no modifications)
    python utilities/sync_sp500.py --check

    # Apply changes to database
    python utilities/sync_sp500.py --sync

    # Force refresh even if recently checked
    python utilities/sync_sp500.py --sync --force
"""

import sys
import os
import argparse
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional, Set
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SP500Syncer:
    """Handles S&P 500 composition fetching and database synchronization"""

    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")

        logger.info(f"✅ Connected to database: {db_path}")

    def fetch_sp500_symbols(self) -> Tuple[Optional[List[str]], Dict[str, any]]:
        """
        Fetch current S&P 500 symbols using multiple reliable sources

        Returns:
            (symbol_list, metadata_dict) or (None, error_dict)
        """
        # Try Method 1: SlickCharts (most reliable in testing)
        try:
            logger.info("📊 Fetching from SlickCharts...")
            symbols, metadata = self._fetch_from_slickcharts()
            if symbols and len(symbols) >= 500:
                logger.info(f"✅ SUCCESS: {len(symbols)} symbols from SlickCharts")
                return symbols, metadata
        except Exception as e:
            logger.warning(f"SlickCharts failed: {e}")

        # Try Method 2: Wikipedia with headers
        try:
            logger.info("📊 Fetching from Wikipedia...")
            symbols, metadata = self._fetch_from_wikipedia()
            if symbols and len(symbols) >= 500:
                logger.info(f"✅ SUCCESS: {len(symbols)} symbols from Wikipedia")
                return symbols, metadata
        except Exception as e:
            logger.warning(f"Wikipedia failed: {e}")

        # Try Method 3: CBOE (if we implement parsing)
        # Future enhancement

        logger.error("❌ All fetching methods failed")
        return None, {'error': 'All sources failed', 'timestamp': datetime.now().isoformat()}

    def _fetch_from_slickcharts(self) -> Tuple[List[str], Dict]:
        """Fetch from SlickCharts (most reliable)"""
        url = "https://www.slickcharts.com/sp500"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse table
        tables = pd.read_html(StringIO(response.text))

        if not tables or len(tables) == 0:
            raise ValueError("No tables found in SlickCharts response")

        sp500_table = tables[0]

        if 'Symbol' not in sp500_table.columns:
            raise ValueError("No Symbol column found in SlickCharts table")

        symbols = sp500_table['Symbol'].tolist()

        # Clean symbols
        clean_symbols = []
        for symbol in symbols:
            if pd.notna(symbol) and isinstance(symbol, str):
                clean_symbol = symbol.replace('.', '-').strip()
                clean_symbols.append(clean_symbol)

        metadata = {
            'source': 'SlickCharts',
            'url': url,
            'fetch_date': datetime.now().isoformat(),
            'total_symbols': len(clean_symbols),
            'method': 'html_table_scraping'
        }

        return clean_symbols, metadata

    def _fetch_from_wikipedia(self) -> Tuple[List[str], Dict]:
        """Fetch from Wikipedia with proper headers"""
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse table
        tables = pd.read_html(StringIO(response.text))

        if not tables or len(tables) == 0:
            raise ValueError("No tables found in Wikipedia response")

        sp500_table = tables[0]

        # Find symbol column (handle different column types)
        symbol_col = None
        for col in sp500_table.columns:
            col_str = str(col).lower()
            if 'symbol' in col_str or 'ticker' in col_str:
                symbol_col = col
                break

        if symbol_col is None:
            # Fallback to first column
            symbol_col = sp500_table.columns[0]

        symbols = sp500_table[symbol_col].tolist()

        # Clean symbols
        clean_symbols = []
        for symbol in symbols:
            if pd.notna(symbol) and isinstance(symbol, str):
                clean_symbol = symbol.replace('.', '-').strip()
                clean_symbols.append(clean_symbol)

        metadata = {
            'source': 'Wikipedia',
            'url': url,
            'fetch_date': datetime.now().isoformat(),
            'total_symbols': len(clean_symbols),
            'method': 'html_table_scraping'
        }

        return clean_symbols, metadata

    def get_database_stocks(self) -> Tuple[Set[str], Set[str]]:
        """
        Get stocks from database

        Returns:
            (all_symbols, active_symbols)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all stocks
        cursor.execute("SELECT symbol FROM stocks")
        all_symbols = set(row[0] for row in cursor.fetchall())

        # Get active stocks
        cursor.execute("SELECT symbol FROM stocks WHERE is_active = 1")
        active_symbols = set(row[0] for row in cursor.fetchall())

        conn.close()

        logger.info(f"💾 Database: {len(all_symbols)} total, {len(active_symbols)} active")
        return all_symbols, active_symbols

    def detect_changes(self, current_sp500: Set[str], database_active: Set[str]) -> Dict[str, List[str]]:
        """
        Detect changes between current S&P 500 and database

        Returns:
            Dictionary with 'added' and 'removed' lists
        """
        added = list(current_sp500 - database_active)
        removed = list(database_active - current_sp500)

        logger.info(f"\n{'='*70}")
        logger.info(f"CHANGE DETECTION")
        logger.info(f"{'='*70}")
        logger.info(f"Current S&P 500: {len(current_sp500)} stocks")
        logger.info(f"Database active: {len(database_active)} stocks")
        logger.info(f"Added: {len(added)} stocks")
        logger.info(f"Removed: {len(removed)} stocks")

        if added:
            logger.info(f"\n➕ NEW STOCKS: {', '.join(added)}")

        if removed:
            logger.info(f"\n➖ REMOVED STOCKS: {', '.join(removed)}")

        return {
            'added': added,
            'removed': removed,
            'current_total': len(current_sp500),
            'database_total': len(database_active)
        }

    def apply_changes(self, changes: Dict[str, List[str]], dry_run: bool = True) -> Dict[str, int]:
        """
        Apply changes to database

        Args:
            changes: Dictionary with 'added' and 'removed' lists
            dry_run: If True, don't actually modify database

        Returns:
            Statistics of changes applied
        """
        added = changes['added']
        removed = changes['removed']

        if dry_run:
            logger.info(f"\n{'='*70}")
            logger.info(f"DRY RUN: Would make the following changes")
            logger.info(f"{'='*70}")
            logger.info(f"Mark as inactive (is_active=0): {len(removed)} stocks")
            logger.info(f"Add new stocks: {len(added)} stocks")
            logger.info(f"\nRun with --sync flag to apply changes")
            return {'removed': 0, 'added': 0}

        logger.info(f"\n{'='*70}")
        logger.info(f"APPLYING CHANGES TO DATABASE")
        logger.info(f"{'='*70}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Mark removed stocks as inactive
        removed_count = 0
        if removed:
            logger.info(f"\n➖ Marking {len(removed)} stocks as inactive...")
            for symbol in removed:
                cursor.execute("""
                    UPDATE stocks
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = ?
                """, (symbol,))
                removed_count += cursor.rowcount

            logger.info(f"✅ Marked {removed_count} stocks as inactive")

        # Add new stocks (basic entry, full data collected separately)
        added_count = 0
        if added:
            logger.info(f"\n➕ Adding {len(added)} new stocks to database...")

            # Import yfinance for stock info
            import yfinance as yf
            import time

            for symbol in added:
                try:
                    # Get basic info from Yahoo Finance
                    ticker = yf.Ticker(symbol)
                    info = ticker.info

                    if not info or len(info) < 5:
                        logger.warning(f"⚠️  Skipping {symbol}: No data available")
                        continue

                    # Extract stock information
                    company_name = info.get('longName') or info.get('shortName', f"{symbol} Inc.")
                    sector = info.get('sector', 'Unknown')
                    industry = info.get('industry', 'Unknown')
                    market_cap = info.get('marketCap')
                    exchange = info.get('exchange', 'UNKNOWN')

                    # Insert into database
                    cursor.execute("""
                        INSERT OR REPLACE INTO stocks
                        (symbol, company_name, sector, industry, market_cap, listing_exchange, is_active, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    """, (symbol, company_name, sector, industry, market_cap, exchange))

                    added_count += 1
                    logger.info(f"  ✅ Added {symbol}: {company_name}")

                    time.sleep(0.1)  # Rate limiting

                except Exception as e:
                    logger.error(f"  ❌ Error adding {symbol}: {e}")

            conn.commit()
            logger.info(f"✅ Successfully added {added_count}/{len(added)} stocks to database")
        else:
            conn.commit()

        conn.close()

        logger.info(f"\n{'='*70}")
        logger.info(f"SYNC COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Stocks marked inactive: {removed_count}")
        logger.info(f"Stocks added: {added_count}")

        return {'removed': removed_count, 'added': added_count}


def main():
    """Main sync script"""
    parser = argparse.ArgumentParser(description='Sync S&P 500 composition with database')
    parser.add_argument('--check', action='store_true',
                       help='Check for changes without applying (default)')
    parser.add_argument('--sync', action='store_true',
                       help='Apply changes to database')
    parser.add_argument('--force', action='store_true',
                       help='Force refresh even if recently checked')
    parser.add_argument('--db-path', default='data/stock_data.db',
                       help='Path to database (default: data/stock_data.db)')

    args = parser.parse_args()

    # Initialize syncer
    try:
        syncer = SP500Syncer(db_path=args.db_path)
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return 1

    # Fetch current S&P 500
    logger.info("🔍 Fetching current S&P 500 composition...")
    current_symbols, metadata = syncer.fetch_sp500_symbols()

    if not current_symbols:
        logger.error("❌ Failed to fetch S&P 500 symbols")
        logger.error(f"Error: {metadata.get('error', 'Unknown error')}")
        return 1

    logger.info(f"📊 Fetched {len(current_symbols)} symbols from {metadata['source']}")

    # Get database stocks
    all_db_symbols, active_db_symbols = syncer.get_database_stocks()

    # Detect changes
    changes = syncer.detect_changes(set(current_symbols), active_db_symbols)

    # Apply or report changes
    if args.sync:
        results = syncer.apply_changes(changes, dry_run=False)
    else:
        results = syncer.apply_changes(changes, dry_run=True)

    return 0


if __name__ == '__main__':
    sys.exit(main())
