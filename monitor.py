#!/usr/bin/env python3
"""
Lululemon Product Monitor
Monitors Lululemon products for stock availability and price alerts.
Sends email notifications when products come in stock at specified price.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import schedule
import os
from pathlib import Path
import gzip
from typing import Optional, Tuple

class LululemonMonitor:
    def __init__(self, config_file='config.json'):
        """Initialize the monitor with configuration."""
        self.config_file = config_file
        self.state_file = 'monitor_state.json'
        self.config = self.load_config()
        self.state = self.load_state()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            # IMPORTANT: Don't force brotli ("br") here.
            # We've observed cases where the saved "HTML" was actually binary/garbled,
            # which prevents price/stock text like "$108 USD" / "Sold out online." from being parsed.
            # Let `requests` manage Accept-Encoding + decompression automatically.
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Referer': 'https://www.google.com/'
        })

    def _decode_response_body(self, response: requests.Response) -> Tuple[str, str]:
        """
        Best-effort decode of a response body to text.

        Returns: (text, debug_note)
        """
        raw = response.content or b""

        # If body looks gzipped (even if server headers are weird), try to decompress.
        try:
            if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
                raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="replace"), "decoded:gzip->utf8"
        except Exception:
            # Fall through to other decode strategies
            pass

        # Prefer requests' decoding first
        try:
            txt = response.text
            if txt and "<html" in txt.lower():
                return txt, "decoded:requests.text"
        except Exception:
            pass

        # Fallback: try utf-8 then latin-1
        try:
            return raw.decode("utf-8", errors="replace"), "decoded:utf8_replace"
        except Exception:
            return raw.decode("latin-1", errors="replace"), "decoded:latin1_replace"
    
    def load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found. Please create it.")
            return {}
        except json.JSONDecodeError:
            print(f"Error parsing {self.config_file}. Please check the JSON format.")
            return {}
    
    def load_state(self):
        """Load previous monitoring state."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_state(self):
        """Save current monitoring state."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def check_product(self, product_url):
        """Check a product's stock status and price."""
        try:
            # First, make a request to the homepage to establish a session and get cookies
            # This helps bypass bot detection
            try:
                self.session.get('https://shop.lululemon.com/', timeout=5)
                time.sleep(1)  # Small delay between requests
            except:
                pass  # Continue even if homepage request fails
            
            # Update referer to the actual Lululemon domain
            headers = self.session.headers.copy()
            headers['Referer'] = 'https://shop.lululemon.com/'
            headers['Origin'] = 'https://shop.lululemon.com'
            
            response = self.session.get(product_url, timeout=15, headers=headers, allow_redirects=True)
            response.raise_for_status()

            page_text, decode_note = self._decode_response_body(response)
            soup = BeautifulSoup(page_text, 'html.parser')
            import re
            
            # Debug: Save page HTML for inspection (enable debug mode in config.json)
            if self.config.get('debug', False):
                import os
                from urllib.parse import urlparse, parse_qs
                debug_dir = '/tmp/lululemon_debug'
                os.makedirs(debug_dir, exist_ok=True)
                parsed = urlparse(product_url)
                params = parse_qs(parsed.query)
                color_id = params.get('color', ['unknown'])[0]
                # Save raw bytes and decoded HTML so we can compare what the server actually sent.
                raw_file = f'{debug_dir}/color_{color_id}.bin'
                html_file = f'{debug_dir}/color_{color_id}.html'
                try:
                    with open(raw_file, 'wb') as f:
                        f.write(response.content or b'')
                except Exception:
                    pass
                with open(html_file, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(page_text)
                print(f"  [DEBUG] Saved raw to {raw_file}")
                print(f"  [DEBUG] Saved HTML to {html_file} ({decode_note})")
            
            # Try to get product name from config first (urls.json has color names)
            product_name = "Align Legging"
            try:
                # Look up color name from config
                for product in self.config.get('products', []):
                    if product.get('url') == product_url:
                        color_name = product.get('name', '')
                        if color_name:
                            product_name = f"Align Legging - {color_name}"
                            break
            except:
                pass
            
            # Fallback: extract color from URL if available
            if product_name == "Align Legging":
                try:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(product_url)
                    params = parse_qs(parsed.query)
                    color_id = params.get('color', [None])[0]
                    if color_id:
                        product_name = f"Align Legging - Color {color_id}"
                except:
                    pass
            
            current_price = None
            # Default to IN STOCK unless we find "Sold out online."
            is_in_stock = True
            stock_indicators = []
            
            # Strategy 1: Look for "$XXX USD" pattern - PRIORITY to script tags (most reliable)
            # User says "$108 USD" is obvious - search ALL script tags aggressively
            script_tags = soup.find_all('script')
            usd_patterns = [
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+USD',      # "$108 USD" with space
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)USD',         # "$108USD" no space
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',      # "$108 USD" flexible
            ]
            
            # Search ALL script tags (not just ones with USD)
            for script in script_tags:
                if script.string:
                    script_text = script.string
                    for pattern in usd_patterns:
                        match = re.search(pattern, script_text, re.IGNORECASE)
                        if match:
                            try:
                                price_val = float(match.group(1).replace(',', ''))
                                if 20 <= price_val <= 300:
                                    current_price = price_val
                                    stock_indicators.append(f"Price from script '$XXX USD': ${current_price}")
                                    break
                            except:
                                pass
                    if current_price:
                        break
            
            # Strategy 2: Look for embedded JSON data with variant information
            variant_data = None
            for script in script_tags:
                if script.string:
                    script_text = script.string
                    
                    # Try to find JSON-LD structured data
                    if script.get('type') == 'application/ld+json':
                        try:
                            data = json.loads(script_text)
                            if isinstance(data, dict) and data.get('@type') == 'Product':
                                variant_data = data
                                stock_indicators.append("JSON-LD found")
                                break
                        except:
                            pass
                    
                    # Look for embedded product JSON (common e-commerce pattern)
                    # Pattern: window.productData = {...} or __INITIAL_STATE__ = {...}
                    json_patterns = [
                        r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                        r'window\.productData\s*=\s*({.+?});',
                        r'"product":\s*({.+?})',
                        r'"variants":\s*\[({.+?})\]',
                    ]
                    
                    for pattern in json_patterns:
                        match = re.search(pattern, script_text, re.DOTALL)
                        if match:
                            try:
                                data = json.loads(match.group(1) if match.lastindex else match.group(0))
                                if isinstance(data, dict) and ('variants' in data or 'product' in data or 'inventory' in data):
                                    variant_data = data
                                    stock_indicators.append("Embedded JSON found")
                                    break
                            except:
                                pass
                    
                    if variant_data:
                        break
            
            # Strategy 2: If we found JSON data, parse it
            if variant_data:
                # Try to extract from JSON-LD
                if variant_data.get('@type') == 'Product':
                    product_name = variant_data.get('name', product_name)
                    offers = variant_data.get('offers', {})
                    if isinstance(offers, dict):
                        price_val = offers.get('price')
                        if price_val:
                            try:
                                current_price = float(price_val)
                                stock_indicators.append(f"Price from JSON-LD: ${current_price}")
                            except:
                                pass
                        
                        availability = offers.get('availability', '')
                        if availability:
                            is_in_stock = 'InStock' in availability or 'inStock' in availability or 'IN_STOCK' in str(availability).upper()
                            stock_indicators.append(f"Stock from JSON-LD: {availability}")
                
                # Try to extract from embedded variant data
                variants = variant_data.get('variants', [])
                if variants and isinstance(variants, list):
                    # Check if any variant is in stock
                    for variant in variants:
                        if isinstance(variant, dict):
                            variant_available = variant.get('available', variant.get('inStock', variant.get('in_stock')))
                            if variant_available:
                                variant_price = variant.get('price', variant.get('compare_at_price'))
                                if variant_price:
                                    try:
                                        price_val = float(str(variant_price).replace('$', '').replace(',', ''))
                                        if current_price is None or price_val < current_price:
                                            current_price = price_val
                                    except:
                                        pass
                                if variant_available == True or str(variant_available).lower() in ['true', 'in stock', 'available']:
                                    is_in_stock = True
                                    stock_indicators.append("Variant data shows in stock")
                                    break
            
            # Strategy 3: Parse HTML elements for stock status
            # Look for product title - try multiple strategies
            title_element = (soup.find('h1', {'data-testid': 'product-title'}) or
                           soup.find('h1', class_=lambda x: x and ('product' in x.lower() or 'title' in x.lower())) or
                           soup.find('h1'))
            
            if title_element:
                # Keep the config-based name ("Align Legging - <Color>") stable.
                # Only record the on-page title as a debug indicator.
                title_text = title_element.get_text(strip=True)
                if title_text and title_text != "" and len(title_text) > 3:
                    stock_indicators.append(f"Title found: {title_text[:80]}")
                else:
                    # Try finding title in page text patterns
                    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', page_text, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        title_text = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                        if title_text and len(title_text) > 3:
                            stock_indicators.append(f"Title from regex: {title_text[:80]}")
            
            # Search page text for "$XXX USD" (after script tags, fallback)
            # Only if not found in script tags
            if current_price is None:
                for pattern in usd_patterns:
                    usd_price_match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                    if usd_price_match:
                        try:
                            price_val = float(usd_price_match.group(1).replace(',', ''))
                            if 20 <= price_val <= 300:
                                current_price = price_val
                                stock_indicators.append(f"Price from '$XXX USD' pattern: ${current_price}")
                                break
                        except:
                            continue
            
            # Also search in soup text (handles HTML entities, non-breaking spaces)
            if current_price is None:
                soup_text = soup.get_text()
                for pattern in usd_patterns:
                    usd_price_match = re.search(pattern, soup_text, re.IGNORECASE | re.MULTILINE)
                    if usd_price_match:
                        try:
                            price_val = float(usd_price_match.group(1).replace(',', ''))
                            if 20 <= price_val <= 300:
                                current_price = price_val
                                stock_indicators.append(f"Price from '$XXX USD' (soup text): ${current_price}")
                                break
                        except:
                            continue
            
            # Look for price elements (multiple strategies)
            if current_price is None:
                price_element = (soup.find('span', {'data-testid': 'price'}) or
                               soup.find('span', class_=lambda x: x and 'price' in x.lower()) or
                               soup.find('div', {'data-testid': 'price'}) or
                               soup.find('p', class_=lambda x: x and 'price' in x.lower()))
                
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    # Look for $XXX pattern in price text
                    price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_text.replace(',', ''))
                    if price_match:
                        try:
                            price_val = float(price_match.group(1))
                            if price_val >= 20 and price_val <= 300:  # Realistic range
                                current_price = price_val
                                stock_indicators.append(f"Price from HTML: ${current_price}")
                        except:
                            pass
            
            # Look for meta tags with price
            if current_price is None:
                price_meta = (soup.find('meta', property='product:price:amount') or
                            soup.find('meta', {'name': 'price'}) or
                            soup.find('meta', {'property': 'og:price:amount'}))
                if price_meta:
                    try:
                        price_val = float(price_meta.get('content', 0))
                        if price_val >= 20 and price_val <= 300:
                            current_price = price_val
                            stock_indicators.append(f"Price from meta: ${current_price}")
                    except:
                        pass
            
            # Fallback: search for any $XX or $XXX pattern (realistic range)
            if current_price is None:
                price_pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
                matches = re.findall(price_pattern, page_text)
                if matches:
                    try:
                        # Filter for realistic prices
                        prices = [float(m.replace(',', '')) for m in matches]
                        prices = [p for p in prices if p >= 20 and p <= 300]
                        if prices:
                            # Take the most common price or median
                            current_price = prices[0] if prices else None
                            if current_price:
                                stock_indicators.append(f"Price from page scan: ${current_price}")
                    except:
                        pass
            
            # Stock detection: ONLY check for "Sold out online." text (exact requirement)
            # Default is IN STOCK unless this text appears
            # Search multiple ways to catch it
            sold_out_patterns = [
                r'sold\s+out\s+online\.',        # "sold out online." with spaces
                r'sold\s+out\s+online',          # "sold out online" without period
                r'Sold\s+out\s+online\.',        # Capitalized
            ]
            
            sold_out_found = False
            # Check in raw page text first
            for pattern in sold_out_patterns:
                if re.search(pattern, page_text, re.IGNORECASE):
                    sold_out_found = True
                    break
            
            # Also check in BeautifulSoup extracted text
            if not sold_out_found:
                soup_text = soup.get_text()
                for pattern in sold_out_patterns:
                    if re.search(pattern, soup_text, re.IGNORECASE):
                        sold_out_found = True
                        break
            
            if sold_out_found:
                is_in_stock = False
                stock_indicators.append("'Sold out online.' text found - OUT OF STOCK")
            else:
                # No "Sold out online." found, so it's IN STOCK
                is_in_stock = True
                stock_indicators.append("No 'Sold out online.' text - IN STOCK")
            
            # Debug output (can be enabled via config)
            if self.config.get('debug', False):
                print(f"  Stock indicators: {', '.join(stock_indicators)}")
            
            return {
                'url': product_url,
                'name': product_name,
                'price': current_price,
                'in_stock': is_in_stock,
                'checked_at': datetime.now().isoformat(),
                'indicators': stock_indicators  # For debugging
            }
            
        except requests.RequestException as e:
            print(f"Error fetching {product_url}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing {product_url}: {e}")
            import traceback
            if self.config.get('debug', False):
                traceback.print_exc()
            return None
    
    def get_price_tier(self, price):
        """Determine which price tier a product falls into."""
        if price is None:
            return None
        if price < 50:
            return 'S1'  # Best deal
        elif 50 <= price < 60:
            return 'S2'  # Great deal
        else:
            return None  # Above threshold
    
    def should_send_alert(self, product_info, product_config):
        """Determine if we should send an alert for this product.
        Supports two tiers:
        S1: price < $50, trigger: new S1 - old S1 (wasn't in S1 before)
        S2: price >= $50 and < $60, trigger: new S2 - (old S1 + old S2) (wasn't in S1 or S2 before)
        """
        if not product_info or not product_info.get('in_stock'):
            return None  # No alert
        
        price = product_info.get('price')
        if price is None:
            return None
        
        # Determine current tier
        current_tier = self.get_price_tier(price)
        if current_tier is None:
            return None  # Price is >= $60, no alert
        
        # Get previous state for this product
        product_id = product_info['url']
        last_state = self.state.get('last_alerts', {}).get(product_id, {})
        
        was_in_s1 = last_state.get('was_in_s1', False)
        was_in_s2 = last_state.get('was_in_s2', False)
        
        # S1 Alert: Currently in S1 AND wasn't in S1 before
        if current_tier == 'S1':
            if not was_in_s1:
                return 'S1'  # New S1 - old S1 (wasn't in S1 before)
            return None  # Was already in S1, no new alert
        
        # S2 Alert: Currently in S2 AND wasn't in S1 or S2 before
        elif current_tier == 'S2':
            if not was_in_s1 and not was_in_s2:
                return 'S2'  # New S2 - (old S1 + old S2) (wasn't in either before)
            return None  # Was in S1 or S2 before, no new alert
        
        return None
    
    def send_email(self, product_info, tier):
        """Send email notification about product availability.
        
        Args:
            product_info: Product information dictionary
            tier: 'S1' for Best deal (< $50) or 'S2' for Great deal (>= $50 and < $60)
        """
        if not self.config.get('email'):
            print("Email configuration not found. Skipping email notification.")
            return
        
        email_config = self.config['email']
        
        # Set email subject based on tier
        if tier == 'S1':
            subject = "Best lululemon deal"
        elif tier == 'S2':
            subject = "Great lululemon deal"
        else:
            subject = f"Lululemon Alert: {product_info['name']} In Stock!"
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = email_config['to']
            msg['Subject'] = subject
            
            tier_label = "Best Deal (< $50)" if tier == 'S1' else "Great Deal ($50-$60)"
            
            body = f"""
Product Name: {product_info['name']}
Price: ${product_info['price']:.2f}
Tier: {tier_label}
Status: In Stock
URL: {product_info['url']}

Checked at: {product_info['checked_at']}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            if email_config.get('use_smtp'):
                # Custom SMTP server
                server = smtplib.SMTP(email_config['smtp_host'], email_config.get('smtp_port', 587))
                if email_config.get('smtp_tls', True):
                    server.starttls()
                if email_config.get('smtp_username'):
                    server.login(email_config['smtp_username'], email_config['smtp_password'])
                server.send_message(msg)
                server.quit()
            else:
                # Gmail SMTP (default)
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_config['from'], email_config['password'])
                server.send_message(msg)
                server.quit()
            
            tier_name = "Best Deal (S1)" if tier == 'S1' else "Great Deal (S2)"
            print(f"✅ Email sent ({tier_name}) for {product_info['name']}")
            
            # Update state to record this alert and tier status
            product_id = product_info['url']
            if 'last_alerts' not in self.state:
                self.state['last_alerts'] = {}
            
            current_tier = self.get_price_tier(product_info['price'])
            
            # Update state: mark that product was in this tier
            self.state['last_alerts'][product_id] = {
                'price': product_info['price'],
                'in_stock': product_info['in_stock'],
                'was_in_s1': (current_tier == 'S1'),
                'was_in_s2': (current_tier == 'S2'),
                'last_tier': current_tier,
                'last_alerted_tier': tier,
                'alerted_at': datetime.now().isoformat()
            }
            self.save_state()
            
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def check_all_products(self):
        """Check all products in the configuration."""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking products...")
        
        products = self.config.get('products', [])
        
        for product in products:
            url = product.get('url')
            if not url:
                continue
            
            print(f"Checking: {url}")
            product_info = self.check_product(url)
            
            if product_info:
                print(f"  Name: {product_info.get('name', 'Unknown')}")
                print(f"  Price: ${product_info.get('price', 'N/A')}")
                print(f"  In Stock: {product_info.get('in_stock', False)}")
                
                # Determine which tier (if any) should trigger an alert
                alert_tier = self.should_send_alert(product_info, product)
                
                if alert_tier:
                    tier_name = "Best Deal (S1)" if alert_tier == 'S1' else "Great Deal (S2)"
                    print(f"  ✅ ALERT! Sending {tier_name} notification...")
                    self.send_email(product_info, alert_tier)
                else:
                    # Still update state even if no alert (to track current tier status)
                    if product_info.get('in_stock'):
                        current_tier = self.get_price_tier(product_info.get('price'))
                        if current_tier:
                            product_id = product_info['url']
                            if 'last_alerts' not in self.state:
                                self.state['last_alerts'] = {}
                            if product_id not in self.state['last_alerts']:
                                self.state['last_alerts'][product_id] = {}
                            
                            # Update tier status without sending alert
                            self.state['last_alerts'][product_id]['was_in_s1'] = (current_tier == 'S1')
                            self.state['last_alerts'][product_id]['was_in_s2'] = (current_tier == 'S2')
                            self.state['last_alerts'][product_id]['price'] = product_info.get('price')
                            self.state['last_alerts'][product_id]['in_stock'] = product_info.get('in_stock')
                            self.state['last_alerts'][product_id]['last_tier'] = current_tier
                            self.save_state()
                    
                    print(f"  ⏭️  No alert needed")
            else:
                print(f"  ❌ Failed to check product")
            
            # Be respectful - don't hammer the server
            time.sleep(2)
        
        print("Check complete.\n")
    
    def run(self, interval_minutes=15):
        """Run the monitor continuously with scheduled checks."""
        print(f"Starting Lululemon Monitor...")
        print(f"Will check products every {interval_minutes} minutes")
        print(f"Press Ctrl+C to stop\n")
        
        # Run initial check
        self.check_all_products()
        
        # Schedule checks
        schedule.every(interval_minutes).minutes.do(self.check_all_products)
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute if it's time to run
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            print("Goodbye!")


def main():
    """Main entry point."""
    import sys
    
    # Check for --run-once flag
    run_once = '--run-once' in sys.argv
    
    # Check if config file exists (can be passed as argument)
    config_args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    config_file = config_args[0] if config_args else 'config.json'
    
    if not os.path.exists(config_file):
        print(f"Error: Config file '{config_file}' not found.")
        print("Please create a config.json file. See config.example.json for a template.")
        return
    
    monitor = LululemonMonitor(config_file)
    
    if run_once:
        # Run once and exit (useful for cron jobs)
        print("Running single check...")
        monitor.check_all_products()
    else:
        # Run continuously with scheduler
        interval = monitor.config.get('check_interval_minutes', 15)
        monitor.run(interval)


if __name__ == '__main__':
    main()
