#!/usr/bin/env python3
"""
Reddit Database Cleanup Script

Applies new validation logic to existing reddit_posts to identify and remove false positives.

Usage:
    # Dry run - show what would be removed (safe)
    python utilities/cleanup_reddit_database.py --dry-run

    # Review specific symbols
    python utilities/cleanup_reddit_database.py --dry-run --symbols A IT ON SO NOW

    # Actually remove false positives (with backup)
    python utilities/cleanup_reddit_database.py --remove --backup
"""

import sys
import os
import re
import sqlite3
import shutil
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RedditDatabaseCleaner:
    """Clean up false positive reddit posts from database"""

    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.company_names = self._load_company_names()
        logger.info(f"✅ Connected to database: {db_path}")

    def _load_company_names(self) -> Dict[str, str]:
        """Load ticker -> company name mapping"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, company_name FROM stocks")
        mapping = dict(cursor.fetchall())
        conn.close()
        logger.info(f"✅ Loaded {len(mapping)} company names")
        return mapping

    def _extract_company_keywords(self, company_name: str) -> List[str]:
        """Extract meaningful keywords from company name"""
        if not company_name:
            return []

        # Remove common suffixes
        common_suffixes = [
            'INC.', 'INC', 'CORP.', 'CORP', 'CORPORATION', 'LTD.', 'LTD',
            'LIMITED', 'LLC', 'L.L.C.', 'PLC', 'CO.', 'COMPANY', 'GROUP',
            'HOLDINGS', 'THE', ','
        ]

        name_upper = company_name.upper()
        for suffix in common_suffixes:
            name_upper = name_upper.replace(suffix, '')

        # Split into words and filter
        words = name_upper.split()
        keywords = [w.strip() for w in words if len(w.strip()) > 3]

        return keywords[:2]  # Return top 2 meaningful words

    def validate_post(self, text: str, symbol: str, company_name: str = None) -> Tuple[bool, str]:
        """
        Validate if post is a true mention of the stock

        Returns:
            (is_valid, reason) tuple
        """
        text_upper = text.upper()
        symbol_upper = symbol.upper()

        # Tier 1: Dollar sign prefix (ALWAYS valid)
        if f"${symbol_upper}" in text_upper:
            return (True, "Tier 1: Dollar sign ($)")

        # Tier 2: Company name mention (ALWAYS valid)
        if company_name:
            company_keywords = self._extract_company_keywords(company_name)
            for keyword in company_keywords:
                if keyword in text_upper:
                    return (True, f"Tier 2: Company name ({keyword})")

        # Tier 3: Word boundary + context validation
        # Check if symbol appears as whole word (not substring)
        word_boundary_pattern = rf'\b{re.escape(symbol_upper)}\b'
        if not re.search(word_boundary_pattern, text_upper):
            return (False, "Failed: Not a whole word")

        # For short tickers (≤3 chars), require stock context
        if len(symbol) <= 3:
            stock_keywords = [
                'STOCK', 'SHARES', 'BUY', 'SELL', 'BOUGHT', 'SOLD',
                'EARNINGS', 'REVENUE', 'PRICE', 'TARGET', 'PT',
                'DD', 'DUE DILIGENCE', 'ANALYSIS', 'CALLS', 'PUTS',
                'OPTIONS', 'POSITION', 'BULLISH', 'BEARISH', 'LONG', 'SHORT',
                'INVEST', 'PORTFOLIO', 'HOLDING', 'TICKER', 'STOCK MARKET',
                'VALUATION', 'P/E', 'EPS', 'DIVIDEND', 'YIELD'
            ]

            has_context = any(keyword in text_upper for keyword in stock_keywords)
            if has_context:
                return (True, "Tier 3: Word boundary + stock context")
            else:
                return (False, "Failed: No stock context for short ticker")

        # Medium/long tickers: word boundary is sufficient
        return (True, "Tier 3: Word boundary match")

    def analyze_database(self, symbols: List[str] = None) -> Dict:
        """
        Analyze all reddit posts and identify false positives

        Args:
            symbols: Optional list of symbols to check (default: all)

        Returns:
            Dictionary with analysis results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query
        if symbols:
            placeholders = ','.join('?' * len(symbols))
            query = f"""
                SELECT id, symbol, title, content, subreddit, created_at
                FROM reddit_posts
                WHERE symbol IN ({placeholders})
                ORDER BY symbol, id
            """
            cursor.execute(query, symbols)
        else:
            cursor.execute("""
                SELECT id, symbol, title, content, subreddit, created_at
                FROM reddit_posts
                ORDER BY symbol, id
            """)

        posts = cursor.fetchall()
        conn.close()

        logger.info(f"📊 Analyzing {len(posts)} posts...")

        # Analyze each post
        results_by_symbol = defaultdict(lambda: {'valid': [], 'invalid': []})

        for row in posts:
            post_id, symbol, title, content, subreddit, created_at = row
            company_name = self.company_names.get(symbol, "")

            # Combine title and content for validation
            text = f"{title or ''} {content or ''}"
            is_valid, reason = self.validate_post(text, symbol, company_name)

            post_data = {
                'id': post_id,
                'symbol': symbol,
                'title': title,
                'content': content,
                'subreddit': subreddit,
                'created_at': created_at,
                'reason': reason
            }

            if is_valid:
                results_by_symbol[symbol]['valid'].append(post_data)
            else:
                results_by_symbol[symbol]['invalid'].append(post_data)

        return dict(results_by_symbol)

    def display_analysis(self, results: Dict):
        """Display analysis results"""
        logger.info(f"\n{'='*80}")
        logger.info(f"DATABASE CLEANUP ANALYSIS")
        logger.info(f"{'='*80}\n")

        total_valid = sum(len(data['valid']) for data in results.values())
        total_invalid = sum(len(data['invalid']) for data in results.values())
        total = total_valid + total_invalid

        logger.info(f"Total posts: {total}")
        logger.info(f"Valid posts: {total_valid} ({total_valid/max(total,1)*100:.1f}%)")
        logger.info(f"False positives: {total_invalid} ({total_invalid/max(total,1)*100:.1f}%)")

        if total_invalid > 0:
            logger.info(f"\n{'─'*80}")
            logger.info(f"FALSE POSITIVES BY SYMBOL")
            logger.info(f"{'─'*80}\n")

            # Sort by number of false positives
            sorted_symbols = sorted(results.items(),
                                  key=lambda x: len(x[1]['invalid']),
                                  reverse=True)

            for symbol, data in sorted_symbols:
                invalid_count = len(data['invalid'])
                valid_count = len(data['valid'])

                if invalid_count > 0:
                    company_name = self.company_names.get(symbol, "Unknown")
                    logger.info(f"{symbol:6} ({company_name[:40]:40}) - {invalid_count:3} false positives, {valid_count:3} valid")

            # Show sample false positives
            logger.info(f"\n{'─'*80}")
            logger.info(f"SAMPLE FALSE POSITIVES (first 20)")
            logger.info(f"{'─'*80}\n")

            all_invalid = []
            for symbol, data in results.items():
                all_invalid.extend(data['invalid'])

            for i, post in enumerate(all_invalid[:20], 1):
                logger.info(f"\n{i}. [{post['symbol']}] {post['title'][:70]}")
                logger.info(f"   Subreddit: {post['subreddit']}")
                logger.info(f"   Reason: {post['reason']}")
                logger.info(f"   ID: {post['id']}")

    def backup_database(self) -> str:
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"

        logger.info(f"📦 Creating backup: {backup_path}")
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"✅ Backup created successfully")

        return backup_path

    def remove_false_positives(self, results: Dict, dry_run: bool = True) -> int:
        """
        Remove false positive posts from database

        Args:
            results: Analysis results from analyze_database()
            dry_run: If True, don't actually delete (default: True)

        Returns:
            Number of posts removed
        """
        # Collect all invalid post IDs
        invalid_ids = []
        for symbol, data in results.items():
            invalid_ids.extend([post['id'] for post in data['invalid']])

        if not invalid_ids:
            logger.info("✅ No false positives to remove")
            return 0

        logger.info(f"\n{'='*80}")
        if dry_run:
            logger.info(f"DRY RUN: Would remove {len(invalid_ids)} false positive posts")
        else:
            logger.info(f"REMOVING {len(invalid_ids)} false positive posts")
        logger.info(f"{'='*80}\n")

        if dry_run:
            logger.info("Run with --remove flag to actually delete these posts")
            return 0

        # Actually remove posts
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Remove from batch_mapping first (foreign key constraint)
        placeholders = ','.join('?' * len(invalid_ids))
        cursor.execute(f"""
            DELETE FROM batch_mapping
            WHERE record_type = 'reddit_posts'
            AND record_id IN ({placeholders})
        """, invalid_ids)
        batch_deleted = cursor.rowcount
        logger.info(f"🗑️  Removed {batch_deleted} batch_mapping entries")

        # Remove from reddit_posts
        cursor.execute(f"""
            DELETE FROM reddit_posts
            WHERE id IN ({placeholders})
        """, invalid_ids)
        posts_deleted = cursor.rowcount
        logger.info(f"🗑️  Removed {posts_deleted} reddit_posts entries")

        conn.commit()
        conn.close()

        logger.info(f"✅ Cleanup complete: {posts_deleted} posts removed")
        return posts_deleted


def main():
    """Main cleanup script"""
    import argparse

    parser = argparse.ArgumentParser(description='Clean up false positive reddit posts')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be removed without actually deleting (default)')
    parser.add_argument('--remove', action='store_true',
                       help='Actually remove false positives from database')
    parser.add_argument('--backup', action='store_true',
                       help='Create database backup before removal (recommended with --remove)')
    parser.add_argument('--symbols', nargs='+',
                       help='Only analyze specific symbols (default: all)')
    parser.add_argument('--db-path', default='data/stock_data.db',
                       help='Path to database (default: data/stock_data.db)')
    parser.add_argument('--yes', action='store_true',
                       help='Skip confirmation prompt (auto-confirm removal)')

    args = parser.parse_args()

    # Initialize cleaner
    try:
        cleaner = RedditDatabaseCleaner(db_path=args.db_path)
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return 1

    # Create backup if requested
    if args.backup and args.remove:
        backup_path = cleaner.backup_database()
        logger.info(f"💾 Backup saved to: {backup_path}\n")

    # Analyze database
    logger.info("🔍 Analyzing database for false positives...")
    results = cleaner.analyze_database(symbols=args.symbols)

    # Display results
    cleaner.display_analysis(results)

    # Remove false positives
    if args.remove:
        # Final confirmation
        total_invalid = sum(len(data['invalid']) for data in results.values())

        logger.info(f"\n{'='*80}")
        logger.info(f"⚠️  WARNING: About to remove {total_invalid} posts from database")
        logger.info(f"{'='*80}\n")

        if args.yes:
            logger.info("✅ Auto-confirmed with --yes flag")
            cleaner.remove_false_positives(results, dry_run=False)
        else:
            response = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
            if response.lower() == 'yes':
                cleaner.remove_false_positives(results, dry_run=False)
            else:
                logger.info("❌ Cleanup cancelled by user")
    else:
        cleaner.remove_false_positives(results, dry_run=True)

    return 0


if __name__ == '__main__':
    sys.exit(main())
