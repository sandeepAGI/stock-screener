"""
Yahoo Finance Community Board Scraper using Selenium
"""

import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

logger = logging.getLogger(__name__)

@dataclass
class CommunityMessage:
    """Container for Yahoo Finance community message data"""
    text: str
    author: str
    timestamp: str
    upvotes: int
    downvotes: int
    replies: int
    symbol: str
    
class YahooFinanceCommunityParser:
    """
    Parser for Yahoo Finance community board messages using CSS selectors
    """
    
    # Common CSS selectors for Yahoo Finance community (may need adjustment)
    MESSAGE_SELECTORS = [
        '[data-testid="message"]',
        '.comment',
        '.discussion-item',
        '.message-container',
        '.conversation-message'
    ]
    
    TEXT_SELECTORS = [
        '.message-text',
        '.comment-text', 
        '.message-body',
        '.discussion-text'
    ]
    
    AUTHOR_SELECTORS = [
        '.message-author',
        '.comment-author',
        '.author-name',
        '.username'
    ]
    
    VOTE_SELECTORS = [
        '.vote-count',
        '.upvote-count',
        '.like-count',
        '.reaction-count'
    ]

class YahooFinanceCommunityScraper:
    """
    Enhanced scraper for Yahoo Finance community discussions with better JS handling
    """
    
    def __init__(self, headless: bool = True, timeout: int = 45):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.parser = YahooFinanceCommunityParser()
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with enhanced anti-detection"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')  # Use new headless mode
            
            # Enhanced anti-detection measures
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # More realistic browser profile
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--accept-lang=en-US,en;q=0.9')
            chrome_options.add_argument('--accept-encoding=gzip, deflate, br')
            
            # Window size for consistent rendering
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Install and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set longer timeouts
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)
            
            # Additional anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            logger.info("Enhanced Chrome WebDriver setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            return False
    
    def _wait_for_page_load(self, url: str) -> bool:
        """Navigate to URL and wait for page to load with enhanced loading strategy"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for basic page structure
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for Yahoo Finance specific elements to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid]")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='fin-']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='yf-']"))
                    )
                )
                logger.info("Yahoo Finance elements detected")
            except TimeoutException:
                logger.warning("Yahoo Finance specific elements not found, proceeding anyway")
            
            # Progressive content loading strategy
            self._trigger_content_loading()
            
            return True
            
        except TimeoutException:
            logger.error(f"Timeout waiting for page to load: {url}")
            return False
        except Exception as e:
            logger.error(f"Error loading page {url}: {str(e)}")
            return False
    
    def _trigger_content_loading(self):
        """Trigger lazy-loaded content using multiple strategies"""
        try:
            # Strategy 1: Progressive scrolling to trigger lazy loading
            logger.info("Triggering content loading with scrolling...")
            
            # Get page height for scrolling
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll in steps to trigger lazy loading
            scroll_steps = 5
            for i in range(scroll_steps):
                scroll_position = (total_height // scroll_steps) * (i + 1)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(1)  # Wait for content to load
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Strategy 2: Wait for specific indicators of community content
            community_indicators = [
                "community", "discussion", "conversation", "forum", 
                "message", "comment", "post", "thread"
            ]
            
            page_source = self.driver.page_source.lower()
            found_indicators = [ind for ind in community_indicators if ind in page_source]
            
            if found_indicators:
                logger.info(f"Found community indicators: {found_indicators}")
                # Wait a bit more for dynamic content related to community
                time.sleep(3)
            else:
                logger.warning("No community indicators found in page source")
            
            # Strategy 3: Try to click any "Load more" or "Show more" buttons
            try:
                load_more_selectors = [
                    "button[class*='load']", "button[class*='more']", 
                    "a[class*='load']", "a[class*='more']",
                    "[data-testid*='load']", "[data-testid*='more']"
                ]
                
                for selector in load_more_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                text = element.text.lower()
                                if any(keyword in text for keyword in ['load', 'more', 'show', 'expand']):
                                    logger.info(f"Clicking potential load more button: {text}")
                                    self.driver.execute_script("arguments[0].click();", element)
                                    time.sleep(2)
                                    break
                        except:
                            continue
            except:
                pass  # Continue if clicking fails
                
        except Exception as e:
            logger.debug(f"Error in content loading strategy: {str(e)}")
            # Continue anyway, basic page loading might be sufficient
    
    def _find_messages(self) -> List:
        """Enhanced message finding using multiple strategies"""
        messages = []
        
        # Strategy 1: Try predefined selectors
        for selector in self.parser.MESSAGE_SELECTORS:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} messages using selector: {selector}")
                    messages = elements
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {str(e)}")
        
        # Strategy 2: Enhanced fallback patterns
        if not messages:
            enhanced_selectors = [
                # Yahoo Finance specific patterns
                '[data-testid*="message"]', '[data-testid*="comment"]', '[data-testid*="post"]',
                '[class*="yf-message"]', '[class*="yf-comment"]', '[class*="yf-post"]',
                '[class*="fin-message"]', '[class*="fin-comment"]', '[class*="fin-post"]',
                
                # Generic community patterns
                '[class*="message"]', '[class*="comment"]', '[class*="discussion"]',
                '[class*="post"]', '[class*="thread"]', '[class*="conversation"]',
                
                # Content-based patterns
                'div[role="article"]', 'article', '[role="listitem"]',
                '.content', '.discussion-item', '.forum-post'
            ]
            
            for selector in enhanced_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements using enhanced selector: {selector}")
                        messages = elements
                        break
                except:
                    continue
        
        # Strategy 3: Text-based content analysis
        if not messages:
            logger.info("Trying text-based content analysis...")
            try:
                # Find all divs with substantial text that could be messages
                all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                potential_messages = []
                
                for div in all_divs:
                    try:
                        text = div.text.strip()
                        # Filter for message-like content
                        if (len(text) > 20 and len(text) < 2000 and  # Reasonable length
                            not self._is_navigation_content(text) and  # Not navigation
                            self._looks_like_user_content(text)):  # Looks like user content
                            potential_messages.append(div)
                    except:
                        continue
                
                if potential_messages:
                    logger.info(f"Found {len(potential_messages)} potential messages via text analysis")
                    messages = potential_messages[:20]  # Limit to first 20 to avoid false positives
                    
            except Exception as e:
                logger.debug(f"Text-based analysis failed: {str(e)}")
        
        # Strategy 4: Look for nested content structures
        if not messages:
            logger.info("Trying nested content structure analysis...")
            try:
                # Look for containers that might hold multiple messages
                container_selectors = [
                    '[class*="conversation"]', '[class*="discussion"]', '[class*="forum"]',
                    '[class*="community"]', '[class*="comments"]', '[class*="messages"]'
                ]
                
                for selector in container_selectors:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for container in containers:
                        # Look for child elements that might be individual messages
                        child_messages = container.find_elements(By.XPATH, ".//div[string-length(text()) > 20]")
                        if len(child_messages) > 1:  # Multiple potential messages in container
                            logger.info(f"Found {len(child_messages)} nested messages in container")
                            messages = child_messages
                            break
                    if messages:
                        break
                        
            except Exception as e:
                logger.debug(f"Nested structure analysis failed: {str(e)}")
                
        return messages
    
    def _is_navigation_content(self, text: str) -> bool:
        """Check if text appears to be navigation/header content"""
        nav_keywords = [
            'yahoo finance', 'sign in', 'portfolio', 'markets', 'research',
            'menu', 'navigation', 'search', 'subscribe', 'premium',
            'news', 'sports', 'mail', 'home', 'weather'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in nav_keywords)
    
    def _looks_like_user_content(self, text: str) -> bool:
        """Check if text looks like user-generated content"""
        # Simple heuristics for user-generated content
        user_indicators = [
            # Financial discussion terms
            'stock', 'price', 'buy', 'sell', 'bullish', 'bearish', 'hold',
            'earnings', 'revenue', 'profit', 'loss', 'target', 'dividend',
            'market', 'trading', 'investment', 'portfolio', 'analysis',
            
            # Opinion/discussion terms
            'think', 'believe', 'opinion', 'agree', 'disagree', 'wonder',
            'expecting', 'hoping', 'worried', 'excited', 'disappointed',
            
            # Question/engagement terms
            'what', 'why', 'how', 'when', 'where', 'anyone', 'thoughts',
            'question', 'help', 'advice', 'experience'
        ]
        
        text_lower = text.lower()
        # Count how many user indicators are present
        indicator_count = sum(1 for indicator in user_indicators if indicator in text_lower)
        
        # Consider it user content if it has multiple indicators or specific patterns
        return (indicator_count >= 2 or 
                '?' in text or '!' in text or  # Questions/exclamations
                len(text.split()) > 10)  # Substantial content
    
    def _extract_message_data(self, element, symbol: str) -> Optional[CommunityMessage]:
        """Extract data from a message element"""
        try:
            # Extract text content
            text = ""
            for selector in self.parser.TEXT_SELECTORS:
                try:
                    text_elem = element.find_element(By.CSS_SELECTOR, selector)
                    text = text_elem.text.strip()
                    if text:
                        break
                except:
                    continue
            
            # Fallback: get all text from element
            if not text:
                text = element.text.strip()
            
            # Skip if no meaningful text
            if not text or len(text) < 10:
                return None
            
            # Extract author
            author = "Unknown"
            for selector in self.parser.AUTHOR_SELECTORS:
                try:
                    author_elem = element.find_element(By.CSS_SELECTOR, selector)
                    author = author_elem.text.strip()
                    if author:
                        break
                except:
                    continue
            
            # Extract vote counts (challenging without knowing exact structure)
            upvotes = 0
            downvotes = 0
            
            # Try to find vote-related elements
            for selector in self.parser.VOTE_SELECTORS:
                try:
                    vote_elems = element.find_elements(By.CSS_SELECTOR, selector)
                    for vote_elem in vote_elems:
                        vote_text = vote_elem.text.strip()
                        if vote_text.isdigit():
                            upvotes = int(vote_text)
                            break
                except:
                    continue
            
            return CommunityMessage(
                text=text,
                author=author,
                timestamp=datetime.now().isoformat(),  # Would need to extract actual timestamp
                upvotes=upvotes,
                downvotes=downvotes,
                replies=0,  # Would need to extract reply count
                symbol=symbol
            )
            
        except Exception as e:
            logger.debug(f"Error extracting message data: {str(e)}")
            return None
    
    def scrape_community_messages(self, symbol: str, max_messages: int = 100) -> List[CommunityMessage]:
        """
        Scrape community messages for a given stock symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            max_messages: Maximum number of messages to scrape
            
        Returns:
            List of CommunityMessage objects
        """
        messages = []
        
        try:
            # Setup WebDriver
            if not self._setup_driver():
                return messages
            
            # Navigate to community page
            community_url = f"https://finance.yahoo.com/quote/{symbol}/community/"
            if not self._wait_for_page_load(community_url):
                return messages
            
            logger.info(f"Attempting to scrape messages for {symbol}")
            
            # Debug: Save page source to understand structure
            page_source = self.driver.page_source
            logger.debug(f"Page source length: {len(page_source)} characters")
            
            # Look for any text that might indicate community content
            if 'community' in page_source.lower() or 'discussion' in page_source.lower():
                logger.info("Found community/discussion references in page")
            else:
                logger.warning("No obvious community content found in page")
            
            # Find message elements
            message_elements = self._find_messages()
            
            if not message_elements:
                logger.warning(f"No message elements found for {symbol}")
                # Log some page content for debugging
                logger.debug(f"Page title: {self.driver.title}")
                logger.debug(f"Current URL: {self.driver.current_url}")
                return messages
            
            # Extract data from each message
            for i, element in enumerate(message_elements[:max_messages]):
                try:
                    message_data = self._extract_message_data(element, symbol)
                    if message_data:
                        messages.append(message_data)
                        logger.debug(f"Extracted message {i+1}: {message_data.text[:50]}...")
                    
                    # Add small delay to avoid overwhelming the page
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.debug(f"Error processing message {i}: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(messages)} messages for {symbol}")
            
        except Exception as e:
            logger.error(f"Error scraping community messages for {symbol}: {str(e)}")
            
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
                
        return messages
    
    def test_page_structure(self, symbol: str) -> Dict[str, any]:
        """
        Test method to understand the page structure
        """
        results = {
            'success': False,
            'page_loaded': False,
            'page_title': '',
            'content_indicators': [],
            'potential_selectors': [],
            'sample_text': ''
        }
        
        try:
            if not self._setup_driver():
                return results
            
            community_url = f"https://finance.yahoo.com/quote/{symbol}/community/"
            
            if self._wait_for_page_load(community_url):
                results['page_loaded'] = True
                results['page_title'] = self.driver.title
                
                # Look for content indicators
                indicators = ['comment', 'message', 'discussion', 'community', 'post', 'conversation']
                page_text = self.driver.page_source.lower()
                
                for indicator in indicators:
                    if indicator in page_text:
                        results['content_indicators'].append(indicator)
                
                # Find potential message containers
                potential_containers = self.driver.find_elements(By.CSS_SELECTOR, '[class*="comment"], [class*="message"], [class*="post"], [class*="discussion"]')
                results['potential_selectors'] = [elem.tag_name + '.' + ' '.join(elem.get_attribute('class').split()) for elem in potential_containers[:5]]
                
                # Get some sample text
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                results['sample_text'] = body_text[:500] + '...' if len(body_text) > 500 else body_text
                
                results['success'] = True
                
        except Exception as e:
            logger.error(f"Error testing page structure: {str(e)}")
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return results

# Convenience function
def scrape_yahoo_community_sentiment(symbol: str, max_messages: int = 50) -> List[CommunityMessage]:
    """
    Convenience function to scrape Yahoo Finance community messages
    
    Args:
        symbol: Stock symbol
        max_messages: Maximum messages to scrape
        
    Returns:
        List of community messages
    """
    scraper = YahooFinanceCommunityScraper(headless=True)
    return scraper.scrape_community_messages(symbol, max_messages)