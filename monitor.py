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

class LululemonMonitor:
    def __init__(self, config_file='config.json'):
        """Initialize the monitor with configuration."""
        self.config_file = config_file
        self.state_file = 'monitor_state.json'
        self.config = self.load_config()
        self.state = self.load_state()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
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
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = response.text
            import re
            
            product_name = "Unknown Product"
            current_price = None
            is_in_stock = False
            stock_indicators = []
            
            # Strategy 1: Look for embedded JSON data with variant information
            # Lululemon often embeds product variant data in script tags
            script_tags = soup.find_all('script')
            variant_data = None
            
            for script in script_tags:
                if script.string:
                    # Look for JSON objects that might contain variant/product data
                    # Common patterns: window.__INITIAL_STATE__, productData, variants, etc.
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
            # Look for product title
            title_element = (soup.find('h1', {'data-testid': 'product-title'}) or
                           soup.find('h1', class_=lambda x: x and ('product' in x.lower() or 'title' in x.lower())) or
                           soup.find('h1'))
            
            if title_element:
                product_name = title_element.get_text(strip=True)
                stock_indicators.append(f"Title found: {product_name[:50]}")
            
            # Look for price elements (multiple strategies)
            price_element = (soup.find('span', {'data-testid': 'price'}) or
                           soup.find('span', class_=lambda x: x and 'price' in x.lower()) or
                           soup.find('div', {'data-testid': 'price'}) or
                           soup.find('p', class_=lambda x: x and 'price' in x.lower()))
            
            if price_element and current_price is None:
                price_text = price_element.get_text(strip=True)
                price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_text.replace(',', ''))
                if price_match:
                    try:
                        current_price = float(price_match.group(1))
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
                        current_price = float(price_meta.get('content', 0))
                        if current_price > 0:
                            stock_indicators.append(f"Price from meta: ${current_price}")
                    except:
                        pass
            
            # Fallback: search entire page for price pattern
            if current_price is None:
                price_pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
                matches = re.findall(price_pattern, page_text)
                if matches:
                    try:
                        # Try first few matches, take the smallest (often the sale price)
                        prices = [float(m.replace(',', '')) for m in matches[:5]]
                        if prices:
                            current_price = min(prices)  # Take the lowest price (could be sale price)
                            stock_indicators.append(f"Price from page scan: ${current_price}")
                    except:
                        pass
            
            # Strategy 4: Check for explicit "Sold out online" text (Lululemon-specific)
            sold_out_text = (soup.find(string=re.compile(r'sold out online', re.I)) or
                            soup.find(string=re.compile(r'sold out online\.', re.I)))
            
            # Strategy 5: Check Add to Bag button status (primary indicator)
            # Look for button with specific text patterns (Lululemon uses these)
            add_to_bag_button = None
            all_buttons = soup.find_all('button')
            
            for button in all_buttons:
                button_text = button.get_text(strip=True).lower()
                # Check for Add to Bag button
                if 'add to bag' in button_text or 'add to cart' in button_text:
                    add_to_bag_button = button
                    break
                # Also check for "Sold out - notify me" pattern (indicates out of stock)
                if 'sold out' in button_text and 'notify' in button_text:
                    add_to_bag_button = button
                    break
            
            # Fallback to data-testid or class-based search
            if not add_to_bag_button:
                add_to_bag_button = (soup.find('button', {'data-testid': 'add-to-bag'}) or
                                    soup.find('button', {'data-testid': 'addToBag'}) or
                                    soup.find('button', class_=lambda x: x and 'add' in x.lower() and ('bag' in x.lower() or 'cart' in x.lower())))
            
            # Also check for other out of stock indicators
            out_of_stock_indicators = (
                soup.find(string=re.compile(r'out of stock', re.I)) or
                soup.find(string=re.compile(r'sold out', re.I)) or
                soup.find(string=re.compile(r'notify me', re.I)) or
                soup.find(class_=lambda x: x and ('out-of-stock' in str(x).lower() or 'sold-out' in str(x).lower()))
            )
            
            # Check for "Sold out online" explicitly first (Lululemon pattern)
            if sold_out_text:
                is_in_stock = False
                stock_indicators.append("'Sold out online' text found")
            elif out_of_stock_indicators:
                is_in_stock = False
                stock_indicators.append("Out of stock indicator found")
            elif add_to_bag_button:
                # Check if button is disabled
                button_disabled = (add_to_bag_button.get('disabled') is not None or
                                 'disabled' in add_to_bag_button.get('class', []) or
                                 'aria-disabled' in add_to_bag_button.attrs)
                
                button_text = add_to_bag_button.get_text(strip=True).lower()
                
                if button_disabled:
                    is_in_stock = False
                    stock_indicators.append("Add to Bag button is disabled")
                elif 'sold out' in button_text and 'notify me' in button_text:
                    # "Sold out - notify me" pattern (Lululemon-specific)
                    is_in_stock = False
                    stock_indicators.append(f"Button text: '{button_text}' indicates out of stock")
                elif 'out of stock' in button_text or 'notify me' in button_text or 'sold out' in button_text:
                    is_in_stock = False
                    stock_indicators.append(f"Button text indicates out of stock: {button_text}")
                elif 'add to bag' in button_text or 'add to cart' in button_text:
                    is_in_stock = True
                    stock_indicators.append(f"Button text: '{button_text}' - In Stock")
                else:
                    # Button exists and is not disabled, assume in stock
                    is_in_stock = True
                    stock_indicators.append(f"Add to Bag button found (enabled) - text: '{button_text}'")
            else:
                # No button found - check for size selector being disabled
                size_selectors = soup.find_all(class_=re.compile(r'size|variant', re.I))
                for selector in size_selectors:
                    if 'disabled' in selector.get('class', []) or selector.get('disabled') is not None:
                        stock_indicators.append("Size selector appears disabled")
                
                # If we couldn't determine stock from JSON, default to False
                if not stock_indicators:
                    stock_indicators.append("Could not determine stock status")
            
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
