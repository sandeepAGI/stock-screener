#!/usr/bin/env python3
"""
Stock Universe Management Module
Manages S&P 500 index tracking, custom stock lists, and universe operations
"""

import pandas as pd
import yfinance as yf
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import json
import csv
from enum import Enum

logger = logging.getLogger(__name__)


class UniverseType(Enum):
    """Types of stock universes"""
    SP500 = "sp500"
    CUSTOM = "custom"
    COMBINED = "combined"
    SECTOR = "sector"
    MARKET_CAP = "market_cap"


@dataclass
class StockInfo:
    """Complete stock information"""
    symbol: str
    company_name: str
    sector: str
    industry: str
    market_cap: Optional[int]
    exchange: str
    added_date: datetime
    is_active: bool
    data_quality_score: float
    last_updated: datetime


@dataclass
class UniverseMetadata:
    """Metadata for a stock universe"""
    universe_id: str
    name: str
    description: str
    universe_type: UniverseType
    created_date: datetime
    last_updated: datetime
    stock_count: int
    auto_sync: bool
    source_url: Optional[str]


class StockUniverseManager:
    """Manages stock universes including S&P 500 and custom lists"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.universes_file = self.data_dir / "stock_universes.json"
        self.sp500_file = self.data_dir / "sp500_current.csv"
        self.sp500_history_file = self.data_dir / "sp500_history.json"
        
        # In-memory storage
        self.universes: Dict[str, Dict[str, Any]] = {}
        self.stock_info: Dict[str, StockInfo] = {}
        
        # Load existing data
        self.load_universes()
    
    def load_universes(self):
        """Load existing universes from storage"""
        try:
            if self.universes_file.exists():
                with open(self.universes_file, 'r') as f:
                    data = json.load(f)
                    self.universes = data.get('universes', {})
                    
                    # Convert datetime strings back to datetime objects
                    for universe_id, universe_data in self.universes.items():
                        if 'stocks' in universe_data:
                            for symbol, stock_data in universe_data['stocks'].items():
                                if isinstance(stock_data, dict):
                                    stock_data['added_date'] = datetime.fromisoformat(stock_data['added_date'])
                                    stock_data['last_updated'] = datetime.fromisoformat(stock_data['last_updated'])
                                    self.stock_info[symbol] = StockInfo(**stock_data)
                        
                        # Convert universe metadata dates
                        if 'metadata' in universe_data:
                            metadata = universe_data['metadata']
                            metadata['created_date'] = datetime.fromisoformat(metadata['created_date'])
                            metadata['last_updated'] = datetime.fromisoformat(metadata['last_updated'])
                            metadata['universe_type'] = UniverseType(metadata['universe_type'])
                            
            logger.info(f"Loaded {len(self.universes)} universes")
        except Exception as e:
            logger.error(f"Error loading universes: {e}")
            self.universes = {}
    
    def save_universes(self):
        """Save universes to storage"""
        try:
            # Convert dataclasses and datetime objects to JSON-serializable format
            data_to_save = {'universes': {}}
            
            for universe_id, universe_data in self.universes.items():
                saved_universe = {
                    'metadata': universe_data['metadata'].copy() if 'metadata' in universe_data else {},
                    'stocks': {}
                }
                
                # Convert metadata
                if 'metadata' in universe_data:
                    metadata = saved_universe['metadata']
                    if isinstance(metadata.get('created_date'), datetime):
                        metadata['created_date'] = metadata['created_date'].isoformat()
                    if isinstance(metadata.get('last_updated'), datetime):
                        metadata['last_updated'] = metadata['last_updated'].isoformat()
                    if isinstance(metadata.get('universe_type'), UniverseType):
                        metadata['universe_type'] = metadata['universe_type'].value
                
                # Convert stock info
                if 'stocks' in universe_data:
                    for symbol, stock_info in universe_data['stocks'].items():
                        if isinstance(stock_info, StockInfo):
                            stock_dict = asdict(stock_info)
                            stock_dict['added_date'] = stock_dict['added_date'].isoformat()
                            stock_dict['last_updated'] = stock_dict['last_updated'].isoformat()
                            saved_universe['stocks'][symbol] = stock_dict
                        elif isinstance(stock_info, dict):
                            # Handle datetime objects in dict
                            stock_dict = stock_info.copy()
                            if 'added_date' in stock_dict and isinstance(stock_dict['added_date'], datetime):
                                stock_dict['added_date'] = stock_dict['added_date'].isoformat()
                            if 'last_updated' in stock_dict and isinstance(stock_dict['last_updated'], datetime):
                                stock_dict['last_updated'] = stock_dict['last_updated'].isoformat()
                            saved_universe['stocks'][symbol] = stock_dict
                        else:
                            saved_universe['stocks'][symbol] = stock_info
                
                data_to_save['universes'][universe_id] = saved_universe
            
            with open(self.universes_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
                
            logger.info(f"Saved {len(self.universes)} universes")
        except Exception as e:
            logger.error(f"Error saving universes: {e}")
    
    def fetch_sp500_symbols(self) -> Tuple[List[str], Dict[str, Any]]:
        """
        Fetch current S&P 500 symbols from reliable source
        
        Returns:
            Tuple of (symbol_list, metadata_dict)
        """
        try:
            # Try Wikipedia first (most reliable and free)
            logger.info("Fetching S&P 500 symbols from Wikipedia...")
            
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            # Read tables from Wikipedia
            tables = pd.read_html(url)
            
            if tables and len(tables) > 0:
                # First table contains the current constituents
                sp500_table = tables[0]
                
                # Extract symbols - column might be 'Symbol' or 'Ticker'
                symbol_col = None
                for col in sp500_table.columns:
                    if 'symbol' in col.lower() or 'ticker' in col.lower():
                        symbol_col = col
                        break
                
                if symbol_col is None:
                    # Fallback to first column
                    symbol_col = sp500_table.columns[0]
                
                symbols = sp500_table[symbol_col].tolist()
                
                # Clean up symbols (remove dots, handle special cases)
                clean_symbols = []
                for symbol in symbols:
                    if pd.notna(symbol) and isinstance(symbol, str):
                        # Handle BRK.B -> BRK-B conversion for Yahoo Finance
                        clean_symbol = symbol.replace('.', '-')
                        clean_symbols.append(clean_symbol.strip())
                
                # Create metadata
                metadata = {
                    'source': 'Wikipedia',
                    'url': url,
                    'fetch_date': datetime.now().isoformat(),
                    'total_symbols': len(clean_symbols),
                    'method': 'html_scraping'
                }
                
                logger.info(f"Successfully fetched {len(clean_symbols)} S&P 500 symbols")
                return clean_symbols, metadata
            
        except Exception as e:
            logger.warning(f"Wikipedia fetch failed: {e}")
        
        # Fallback: Try Yahoo Finance direct method
        try:
            logger.info("Trying Yahoo Finance S&P 500 constituents...")
            
            # Get S&P 500 ETF holdings as backup
            spy = yf.Ticker("SPY")
            holdings = spy.get_holdings()
            
            if holdings is not None and len(holdings) > 400:
                symbols = holdings.index.tolist()
                
                metadata = {
                    'source': 'Yahoo Finance SPY ETF',
                    'fetch_date': datetime.now().isoformat(),
                    'total_symbols': len(symbols),
                    'method': 'etf_holdings'
                }
                
                logger.info(f"Successfully fetched {len(symbols)} symbols from SPY ETF")
                return symbols, metadata
                
        except Exception as e:
            logger.warning(f"Yahoo Finance fetch failed: {e}")
        
        # Fallback: Use hardcoded list from reliable sources
        logger.warning("Using fallback S&P 500 symbol list")
        
        fallback_symbols = [
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH",
            "JNJ", "JPM", "V", "PG", "HD", "MA", "AVGO", "PFE", "BAC", "ABBV",
            "KO", "TMO", "COST", "MRK", "PEP", "WMT", "ADBE", "DIS", "ABT", "CRM",
            "VZ", "LLY", "NFLX", "CMCSA", "NKE", "DHR", "TXN", "ORCL", "NEE", "XOM",
            "CVX", "LIN", "T", "BMY", "UPS", "QCOM", "AMD", "PM", "IBM", "HON",
            # Add more as needed - this is a representative sample
        ]
        
        metadata = {
            'source': 'Fallback Hardcoded List',
            'fetch_date': datetime.now().isoformat(),
            'total_symbols': len(fallback_symbols),
            'method': 'hardcoded_sample',
            'note': 'This is a representative sample, not complete S&P 500'
        }
        
        return fallback_symbols, metadata
    
    def update_sp500_universe(self, force_refresh: bool = False) -> bool:
        """
        Update the S&P 500 universe with current constituents
        
        Args:
            force_refresh: Force fetch even if recently updated
            
        Returns:
            True if update was successful
        """
        try:
            # Check if we need to update
            if not force_refresh and 'sp500' in self.universes:
                last_updated = self.universes['sp500']['metadata'].get('last_updated')
                if isinstance(last_updated, datetime):
                    # Update weekly
                    if datetime.now() - last_updated < timedelta(days=7):
                        logger.info("S&P 500 universe is up to date")
                        return True
            
            logger.info("Updating S&P 500 universe...")
            
            # Fetch current symbols
            symbols, fetch_metadata = self.fetch_sp500_symbols()
            
            if not symbols:
                logger.error("Failed to fetch S&P 500 symbols")
                return False
            
            # Validate symbols with Yahoo Finance (validate all for baseline)
            validated_symbols = self._validate_symbols(symbols)  # Validate all symbols for complete baseline
            
            # Create stock info for each symbol
            stock_info_dict = {}
            for symbol in validated_symbols:
                try:
                    # Get basic info from Yahoo Finance
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    stock_info_dict[symbol] = StockInfo(
                        symbol=symbol,
                        company_name=info.get('longName', info.get('shortName', f"{symbol} Inc.")),
                        sector=info.get('sector', 'Unknown'),
                        industry=info.get('industry', 'Unknown'),
                        market_cap=info.get('marketCap'),
                        exchange=info.get('exchange', 'NASDAQ'),
                        added_date=datetime.now(),
                        is_active=True,
                        data_quality_score=0.8,  # Default, will be updated later
                        last_updated=datetime.now()
                    )
                    
                    # Add to global stock info
                    self.stock_info[symbol] = stock_info_dict[symbol]
                    
                except Exception as e:
                    logger.warning(f"Failed to get info for {symbol}: {e}")
                    # Create minimal info
                    stock_info_dict[symbol] = StockInfo(
                        symbol=symbol,
                        company_name=f"{symbol} Inc.",
                        sector='Unknown',
                        industry='Unknown',
                        market_cap=None,
                        exchange='Unknown',
                        added_date=datetime.now(),
                        is_active=True,
                        data_quality_score=0.5,
                        last_updated=datetime.now()
                    )
                    self.stock_info[symbol] = stock_info_dict[symbol]
            
            # Create universe metadata
            universe_metadata = UniverseMetadata(
                universe_id='sp500',
                name='S&P 500',
                description='Standard & Poor\'s 500 Index constituents',
                universe_type=UniverseType.SP500,
                created_date=datetime.now(),
                last_updated=datetime.now(),
                stock_count=len(stock_info_dict),
                auto_sync=True,
                source_url=fetch_metadata.get('url')
            )
            
            # Store in universes
            self.universes['sp500'] = {
                'metadata': asdict(universe_metadata),
                'stocks': stock_info_dict,
                'fetch_metadata': fetch_metadata
            }
            
            # Save to files
            self.save_universes()
            self._save_sp500_csv(stock_info_dict)
            
            logger.info(f"Successfully updated S&P 500 universe with {len(stock_info_dict)} stocks")
            return True
            
        except Exception as e:
            logger.error(f"Error updating S&P 500 universe: {e}")
            return False
    
    def _validate_symbols(self, symbols: List[str]) -> List[str]:
        """Validate symbols exist and have data"""
        validated = []
        
        logger.info(f"Validating {len(symbols)} symbols...")
        
        for i, symbol in enumerate(symbols):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Basic validation - check if we get meaningful data
                if info and len(info) > 5 and (info.get('symbol') or info.get('longName')):
                    validated.append(symbol)
                else:
                    logger.warning(f"Symbol {symbol} failed validation")
                    
                # Progress update every 50 symbols
                if (i + 1) % 50 == 0:
                    logger.info(f"Validated {i + 1}/{len(symbols)} symbols ({len(validated)} valid)")
                    
                # Small delay to respect rate limits
                time.sleep(0.05)  # 50ms delay
                    
            except Exception as e:
                logger.warning(f"Validation failed for {symbol}: {e}")
        
        logger.info(f"Validation complete: {len(validated)}/{len(symbols)} symbols validated")
        return validated
    
    def _save_sp500_csv(self, stock_info_dict: Dict[str, StockInfo]):
        """Save S&P 500 symbols to CSV for easy access"""
        try:
            with open(self.sp500_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Symbol', 'Company_Name', 'Sector', 'Industry', 'Market_Cap', 'Exchange'])
                
                for symbol, info in stock_info_dict.items():
                    writer.writerow([
                        info.symbol,
                        info.company_name,
                        info.sector,
                        info.industry,
                        info.market_cap or '',
                        info.exchange
                    ])
                    
            logger.info(f"Saved S&P 500 symbols to {self.sp500_file}")
        except Exception as e:
            logger.error(f"Error saving S&P 500 CSV: {e}")
    
    def create_custom_universe(self, 
                             universe_id: str,
                             name: str,
                             description: str,
                             symbols: List[str],
                             universe_type: UniverseType = UniverseType.CUSTOM) -> bool:
        """
        Create a custom stock universe
        
        Args:
            universe_id: Unique identifier for the universe
            name: Display name
            description: Description of the universe
            symbols: List of stock symbols
            universe_type: Type of universe
            
        Returns:
            True if creation was successful
        """
        try:
            logger.info(f"Creating custom universe '{name}' with {len(symbols)} symbols")
            
            # Validate symbols
            validated_symbols = self._validate_symbols(symbols)
            
            if len(validated_symbols) < len(symbols) * 0.8:  # At least 80% should validate
                logger.warning(f"Only {len(validated_symbols)}/{len(symbols)} symbols validated")
            
            # Create stock info for validated symbols
            stock_info_dict = {}
            for symbol in validated_symbols:
                if symbol in self.stock_info:
                    # Use existing info
                    stock_info_dict[symbol] = self.stock_info[symbol]
                else:
                    # Create new info
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        
                        stock_info_dict[symbol] = StockInfo(
                            symbol=symbol,
                            company_name=info.get('longName', info.get('shortName', f"{symbol} Inc.")),
                            sector=info.get('sector', 'Unknown'),
                            industry=info.get('industry', 'Unknown'),
                            market_cap=info.get('marketCap'),
                            exchange=info.get('exchange', 'NASDAQ'),
                            added_date=datetime.now(),
                            is_active=True,
                            data_quality_score=0.7,
                            last_updated=datetime.now()
                        )
                        
                        self.stock_info[symbol] = stock_info_dict[symbol]
                        
                    except Exception as e:
                        logger.warning(f"Failed to get info for {symbol}: {e}")
            
            # Create universe metadata
            universe_metadata = UniverseMetadata(
                universe_id=universe_id,
                name=name,
                description=description,
                universe_type=universe_type,
                created_date=datetime.now(),
                last_updated=datetime.now(),
                stock_count=len(stock_info_dict),
                auto_sync=False,
                source_url=None
            )
            
            # Store in universes
            self.universes[universe_id] = {
                'metadata': asdict(universe_metadata),
                'stocks': stock_info_dict
            }
            
            # Save to storage
            self.save_universes()
            
            logger.info(f"Successfully created custom universe '{name}' with {len(stock_info_dict)} stocks")
            return True
            
        except Exception as e:
            logger.error(f"Error creating custom universe: {e}")
            return False
    
    def get_universe_symbols(self, universe_id: str) -> List[str]:
        """Get list of symbols in a universe"""
        if universe_id in self.universes:
            return list(self.universes[universe_id]['stocks'].keys())
        return []
    
    def get_universe_info(self, universe_id: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a universe"""
        return self.universes.get(universe_id)
    
    def list_universes(self) -> Dict[str, Dict[str, Any]]:
        """List all available universes with metadata"""
        result = {}
        for universe_id, universe_data in self.universes.items():
            metadata = universe_data.get('metadata', {})
            result[universe_id] = {
                'name': metadata.get('name', universe_id),
                'description': metadata.get('description', ''),
                'type': metadata.get('universe_type', 'unknown'),
                'stock_count': metadata.get('stock_count', 0),
                'last_updated': metadata.get('last_updated', ''),
                'auto_sync': metadata.get('auto_sync', False)
            }
        return result
    
    def delete_universe(self, universe_id: str) -> bool:
        """Delete a custom universe (cannot delete sp500)"""
        if universe_id == 'sp500':
            logger.error("Cannot delete S&P 500 universe")
            return False
        
        if universe_id in self.universes:
            del self.universes[universe_id]
            self.save_universes()
            logger.info(f"Deleted universe '{universe_id}'")
            return True
        
        return False
    
    def add_symbols_to_universe(self, universe_id: str, symbols: List[str]) -> bool:
        """Add symbols to an existing universe"""
        if universe_id not in self.universes:
            logger.error(f"Universe '{universe_id}' not found")
            return False
        
        try:
            validated_symbols = self._validate_symbols(symbols)
            universe_data = self.universes[universe_id]
            
            added_count = 0
            for symbol in validated_symbols:
                if symbol not in universe_data['stocks']:
                    # Create stock info if needed
                    if symbol not in self.stock_info:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        
                        self.stock_info[symbol] = StockInfo(
                            symbol=symbol,
                            company_name=info.get('longName', f"{symbol} Inc."),
                            sector=info.get('sector', 'Unknown'),
                            industry=info.get('industry', 'Unknown'),
                            market_cap=info.get('marketCap'),
                            exchange=info.get('exchange', 'NASDAQ'),
                            added_date=datetime.now(),
                            is_active=True,
                            data_quality_score=0.7,
                            last_updated=datetime.now()
                        )
                    
                    universe_data['stocks'][symbol] = self.stock_info[symbol]
                    added_count += 1
            
            # Update metadata
            universe_data['metadata']['stock_count'] = len(universe_data['stocks'])
            universe_data['metadata']['last_updated'] = datetime.now()
            
            self.save_universes()
            logger.info(f"Added {added_count} symbols to universe '{universe_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Error adding symbols to universe: {e}")
            return False
    
    def remove_symbols_from_universe(self, universe_id: str, symbols: List[str]) -> bool:
        """Remove symbols from an existing universe"""
        if universe_id not in self.universes:
            logger.error(f"Universe '{universe_id}' not found")
            return False
        
        try:
            universe_data = self.universes[universe_id]
            removed_count = 0
            
            for symbol in symbols:
                if symbol in universe_data['stocks']:
                    del universe_data['stocks'][symbol]
                    removed_count += 1
            
            # Update metadata
            universe_data['metadata']['stock_count'] = len(universe_data['stocks'])
            universe_data['metadata']['last_updated'] = datetime.now()
            
            self.save_universes()
            logger.info(f"Removed {removed_count} symbols from universe '{universe_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Error removing symbols from universe: {e}")
            return False
    
    def export_universe_csv(self, universe_id: str, file_path: str) -> bool:
        """Export universe to CSV file"""
        if universe_id not in self.universes:
            return False
        
        try:
            universe_data = self.universes[universe_id]
            
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Symbol', 'Company_Name', 'Sector', 'Industry', 'Market_Cap', 'Exchange', 'Added_Date'])
                
                for symbol, stock_info in universe_data['stocks'].items():
                    if isinstance(stock_info, StockInfo):
                        writer.writerow([
                            stock_info.symbol,
                            stock_info.company_name,
                            stock_info.sector,
                            stock_info.industry,
                            stock_info.market_cap or '',
                            stock_info.exchange,
                            stock_info.added_date.strftime('%Y-%m-%d')
                        ])
            
            logger.info(f"Exported universe '{universe_id}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting universe: {e}")
            return False
    
    def import_universe_csv(self, universe_id: str, name: str, file_path: str) -> bool:
        """Import universe from CSV file"""
        try:
            symbols = []
            
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header
                
                for row in reader:
                    if row and len(row) > 0:
                        symbol = row[0].strip().upper()
                        if symbol:
                            symbols.append(symbol)
            
            if symbols:
                return self.create_custom_universe(
                    universe_id=universe_id,
                    name=name,
                    description=f"Imported from {file_path}",
                    symbols=symbols
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error importing universe: {e}")
            return False


# Convenience functions
def get_sp500_symbols() -> List[str]:
    """Get current S&P 500 symbols"""
    manager = StockUniverseManager()
    manager.update_sp500_universe()
    return manager.get_universe_symbols('sp500')


def create_sector_universe(sector: str, data_dir: str = "data") -> List[str]:
    """Create a universe based on sector filtering of S&P 500"""
    manager = StockUniverseManager(data_dir)
    manager.update_sp500_universe()
    
    sp500_stocks = manager.get_universe_info('sp500')
    if not sp500_stocks:
        return []
    
    sector_symbols = []
    for symbol, stock_info in sp500_stocks['stocks'].items():
        if isinstance(stock_info, StockInfo) and stock_info.sector.lower() == sector.lower():
            sector_symbols.append(symbol)
        elif isinstance(stock_info, dict) and stock_info.get('sector', '').lower() == sector.lower():
            sector_symbols.append(symbol)
    
    # Create sector universe
    universe_id = f"sector_{sector.lower().replace(' ', '_')}"
    manager.create_custom_universe(
        universe_id=universe_id,
        name=f"{sector} Sector",
        description=f"S&P 500 stocks in {sector} sector",
        symbols=sector_symbols,
        universe_type=UniverseType.SECTOR
    )
    
    return sector_symbols