"""
Utility functions and helpers for StockAnalyzer Pro
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file. If None, uses default config/config.yaml
        
    Returns:
        Dictionary containing configuration
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing configuration file: {e}")

def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    return logging.getLogger("stock_analyzer")

def get_reddit_credentials() -> Dict[str, str]:
    """
    Get Reddit API credentials from environment variables
    
    Returns:
        Dictionary with Reddit credentials
        
    Raises:
        ValueError: If required credentials are missing
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET") 
    user_agent = os.getenv("REDDIT_USER_AGENT")
    
    if not all([client_id, client_secret, user_agent]):
        raise ValueError(
            "Missing Reddit API credentials. Please set REDDIT_CLIENT_ID, "
            "REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT in your .env file"
        )
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "user_agent": user_agent
    }

def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize a value to 0-100 scale
    
    Args:
        value: Value to normalize
        min_val: Minimum value in the range
        max_val: Maximum value in the range
        
    Returns:
        Normalized score between 0 and 100
    """
    if max_val == min_val:
        return 50.0  # Return neutral score if no variation
    
    normalized = ((value - min_val) / (max_val - min_val)) * 100
    return max(0, min(100, normalized))

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Numerator
        denominator: Denominator  
        default: Default value to return if division by zero
        
    Returns:
        Result of division or default value
    """
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator

def format_large_number(number: float) -> str:
    """
    Format large numbers for display (e.g., 1.5B, 250M)
    
    Args:
        number: Number to format
        
    Returns:
        Formatted string
    """
    if abs(number) >= 1e12:
        return f"{number/1e12:.1f}T"
    elif abs(number) >= 1e9:
        return f"{number/1e9:.1f}B"
    elif abs(number) >= 1e6:
        return f"{number/1e6:.1f}M"
    elif abs(number) >= 1e3:
        return f"{number/1e3:.1f}K"
    else:
        return f"{number:.1f}"