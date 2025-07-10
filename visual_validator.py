#!/usr/bin/env python3
"""
Visual validation tool for flight parser using Playwright
Helps understand discrepancies between JS and HTML parsers
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from fast_flights.core import parse_response, extract_html_enrichments
from selectolax.lexbor import LexborHTMLParser


class MockResponse:
    """Mock response object for testing"""
    def __init__(self, text):
        self.text = text
        self.text_markdown = text
        self.status_code = 200


class FlightVisualValidator:
    def __init__(self, html_content, output_dir="visual_validation"):
        self.html_content = html_content
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def validate(self):
        """Run full visual validation"""
        print("Starting visual validation...")
        
        # Parse data using our parsers
        response = MockResponse(self.html_content)
        
        print("Parsing with JS parser...")
        try:
            js_result = parse_response(response, 'js')
            js_flights = js_result.flights
        except Exception as e:
            print(f"JS parser error: {e}")
            js_flights = []
            
        print("Parsing with HTML parser...")
        html_result = parse_response(response, 'html')
        html_flights = html_result.flights
        
        print("Parsing with Hybrid parser...")
        hybrid_result = parse_response(response, 'hybrid')
        hybrid_flights = hybrid_result.flights
        
        # Get HTML enrichments
        parser = LexborHTMLParser(self.html_content)
        enrichments = extract_html_enrichments(parser, self.html_content)
        
        # Visual validation with Playwright
        async with async_playwright() as p:
            # Use system Chrome instead of bundled browser
            browser = await p.chromium.launch(channel="chrome", headless=True)
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # Create temp HTML file
            temp_html = self.output_dir / f"temp_{self.timestamp}.html"
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(self.html_content)
            
            # Load the HTML
            await page.goto(f"file://{temp_html.absolute()}")
            await page.wait_for_load_state('networkidle')
            
            # Take full page screenshot
            full_screenshot = self.output_dir / f"full_page_{self.timestamp}.png"
            await page.screenshot(path=full_screenshot, full_page=True)
            print(f"Full page screenshot saved to: {full_screenshot}")
            
            # Count visible flights
            print("\nCounting visible flights...")
            visible_flights = await self._count_visible_flights(page)
            
            # Extract flight data visually
            print("Extracting flight data visually...")
            visual_flight_data = await self._extract_visual_flight_data(page)
            
            # Take screenshots of first few flight containers
            await self._screenshot_flight_containers(page)
            
            # Generate report
            report = self._generate_report(
                js_flights, html_flights, hybrid_flights,
                enrichments, visible_flights, visual_flight_data
            )
            
            # Save report
            report_path = self.output_dir / f"validation_report_{self.timestamp}.html"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\nValidation report saved to: {report_path}")
            
            # Cleanup
            await browser.close()
            temp_html.unlink()
            
        return report_path
    
    async def _count_visible_flights(self, page):
        """Count flights visible on the page"""
        counts = {}
        
        # Count flight containers
        containers = await page.query_selector_all('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
        counts['containers'] = len(containers)
        
        # Count flight items
        all_flight_items = await page.query_selector_all('ul.Rk10dc li')
        counts['total_items'] = len(all_flight_items)
        
        # Count items per container
        counts['items_per_container'] = []
        for container in containers:
            items = await container.query_selector_all('ul.Rk10dc li')
            counts['items_per_container'].append(len(items))
        
        # Count visible prices (good indicator of actual flights)
        prices = await page.query_selector_all('.YMlIz.FpEdX')
        counts['visible_prices'] = len(prices)
        
        return counts
    
    async def _extract_visual_flight_data(self, page):
        """Extract flight data as seen visually"""
        visual_flights = []
        
        # Get all flight items
        items = await page.query_selector_all('ul.Rk10dc li')
        
        for i, item in enumerate(items[:10]):  # First 10 for analysis
            try:
                flight_data = {}
                
                # Get airline name
                name_elem = await item.query_selector('div.sSHqwe.tPgKwe.ogfYpf span')
                if name_elem:
                    flight_data['name'] = await name_elem.text_content()
                
                # Get times
                time_elems = await item.query_selector_all('span.mv1WYe div')
                if len(time_elems) >= 2:
                    flight_data['departure'] = await time_elems[0].text_content()
                    flight_data['arrival'] = await time_elems[1].text_content()
                
                # Get price
                price_elem = await item.query_selector('.YMlIz.FpEdX')
                if price_elem:
                    flight_data['price'] = await price_elem.text_content()
                
                # Get stops
                stops_elem = await item.query_selector('.BbR8Ec .ogfYpf')
                if stops_elem:
                    flight_data['stops'] = await stops_elem.text_content()
                
                # Get arrival time ahead
                time_ahead_elem = await item.query_selector('span.bOzv6')
                if time_ahead_elem:
                    flight_data['arrival_time_ahead'] = await time_ahead_elem.text_content()
                
                visual_flights.append(flight_data)
                
            except Exception as e:
                print(f"Error extracting flight {i}: {e}")
                
        return visual_flights
    
    async def _screenshot_flight_containers(self, page):
        """Take screenshots of individual flight containers"""
        containers = await page.query_selector_all('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
        
        for i, container in enumerate(containers[:3]):  # First 3 containers
            try:
                screenshot_path = self.output_dir / f"container_{i}_{self.timestamp}.png"
                await container.screenshot(path=screenshot_path)
                print(f"Container {i} screenshot saved")
            except Exception as e:
                print(f"Error screenshotting container {i}: {e}")
    
    def _generate_report(self, js_flights, html_flights, hybrid_flights, 
                        enrichments, visible_counts, visual_flight_data):
        """Generate HTML report"""
        report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Flight Parser Visual Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric .value {{ font-size: 24px; font-weight: bold; }}
        .metric .label {{ color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .success {{ background-color: #d4edda; }}
        .warning {{ background-color: #fff3cd; }}
        .error {{ background-color: #f8d7da; }}
        .flight-sample {{ margin: 10px 0; padding: 10px; background: #f9f9f9; }}
        img {{ max-width: 100%; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>Flight Parser Visual Validation Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <div class="section">
        <h2>Parser Comparison</h2>
        <div class="metric">
            <div class="value">{len(js_flights)}</div>
            <div class="label">JS Parser Flights</div>
        </div>
        <div class="metric">
            <div class="value">{len(html_flights)}</div>
            <div class="label">HTML Parser Flights</div>
        </div>
        <div class="metric">
            <div class="value">{len(hybrid_flights)}</div>
            <div class="label">Hybrid Parser Flights</div>
        </div>
        <div class="metric">
            <div class="value">{len(enrichments)}</div>
            <div class="label">HTML Enrichments</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Visual Counts</h2>
        <div class="metric">
            <div class="value">{visible_counts['containers']}</div>
            <div class="label">Flight Containers</div>
        </div>
        <div class="metric">
            <div class="value">{visible_counts['total_items']}</div>
            <div class="label">Total Flight Items</div>
        </div>
        <div class="metric">
            <div class="value">{visible_counts['visible_prices']}</div>
            <div class="label">Visible Prices</div>
        </div>
        <p>Items per container: {visible_counts['items_per_container']}</p>
    </div>
    
    <div class="section">
        <h2>Discrepancy Analysis</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Status</th>
            </tr>
            <tr class="{'success' if len(js_flights) == len(html_flights) else 'error'}">
                <td>JS vs HTML flight count</td>
                <td>{len(js_flights)} vs {len(html_flights)} (diff: {abs(len(js_flights) - len(html_flights))})</td>
                <td>{'Match' if len(js_flights) == len(html_flights) else 'Mismatch'}</td>
            </tr>
            <tr class="{'success' if len(hybrid_flights) == len(js_flights) else 'warning'}">
                <td>Hybrid vs JS flight count</td>
                <td>{len(hybrid_flights)} vs {len(js_flights)}</td>
                <td>{'Match' if len(hybrid_flights) == len(js_flights) else 'Mismatch'}</td>
            </tr>
            <tr>
                <td>Visual items vs HTML flights</td>
                <td>{visible_counts['total_items']} vs {len(html_flights)}</td>
                <td>{'Close' if abs(visible_counts['total_items'] - len(html_flights)) < 5 else 'Different'}</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Visual Flight Samples</h2>
        <p>First 5 flights as extracted visually from the page:</p>
        """
        
        for i, flight in enumerate(visual_flight_data[:5]):
            report += f"""
        <div class="flight-sample">
            <h4>Visual Flight {i+1}</h4>
            <table>
                <tr>
                    <td><strong>Airline:</strong> {flight.get('name', 'N/A')}</td>
                    <td><strong>Departure:</strong> {flight.get('departure', 'N/A')}</td>
                    <td><strong>Arrival:</strong> {flight.get('arrival', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>Price:</strong> {flight.get('price', 'N/A')}</td>
                    <td><strong>Stops:</strong> {flight.get('stops', 'N/A')}</td>
                    <td><strong>+Days:</strong> {flight.get('arrival_time_ahead', 'N/A')}</td>
                </tr>
            </table>
        </div>
            """
        
        # Add enrichment analysis
        enrichments_with_time = sum(1 for e in enrichments if 'arrival_time_ahead' in e)
        report += f"""
    </div>
    
    <div class="section">
        <h2>Enrichment Analysis</h2>
        <table>
            <tr>
                <th>Enrichment Type</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
            <tr>
                <td>With arrival_time_ahead</td>
                <td>{enrichments_with_time}</td>
                <td>{enrichments_with_time / len(enrichments) * 100:.1f}%</td>
            </tr>
            <tr>
                <td>With emissions</td>
                <td>{sum(1 for e in enrichments if 'emissions' in e)}</td>
                <td>{sum(1 for e in enrichments if 'emissions' in e) / len(enrichments) * 100:.1f}%</td>
            </tr>
            <tr>
                <td>With operated_by</td>
                <td>{sum(1 for e in enrichments if 'operated_by' in e)}</td>
                <td>{sum(1 for e in enrichments if 'operated_by' in e) / len(enrichments) * 100:.1f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Hybrid Parser Performance</h2>
        """
        
        # Check arrival_time_ahead in different parsers
        html_with_time = sum(1 for f in html_flights if f.arrival_time_ahead and f.arrival_time_ahead.strip())
        hybrid_with_time = sum(1 for f in hybrid_flights if f.arrival_time_ahead and f.arrival_time_ahead.strip())
        
        report += f"""
        <table>
            <tr>
                <th>Field</th>
                <th>HTML Parser</th>
                <th>Hybrid Parser</th>
                <th>Status</th>
            </tr>
            <tr class="{'success' if hybrid_with_time >= html_with_time else 'error'}">
                <td>arrival_time_ahead</td>
                <td>{html_with_time} ({html_with_time/len(html_flights)*100:.1f}%)</td>
                <td>{hybrid_with_time} ({hybrid_with_time/len(hybrid_flights)*100:.1f}%)</td>
                <td>{'✓' if hybrid_with_time >= html_with_time else '✗ Hybrid has fewer!'}</td>
            </tr>
        </table>
        
        <h3>Key Findings</h3>
        <ul>
            <li>JS parser finds {len(js_flights)} flights while HTML finds {len(html_flights)} (diff: {abs(len(js_flights) - len(html_flights))})</li>
            <li>Visual count shows {visible_counts['total_items']} flight items on page</li>
            <li>HTML enrichments: {len(enrichments)} items, {enrichments_with_time} with arrival_time_ahead</li>
            <li>Hybrid mode extracts {hybrid_with_time} arrival_time_ahead vs HTML's {html_with_time}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Screenshots</h2>
        <p>Check the output directory for:</p>
        <ul>
            <li>full_page_{self.timestamp}.png - Full page screenshot</li>
            <li>container_0_{self.timestamp}.png - First flight container</li>
            <li>container_1_{self.timestamp}.png - Second flight container</li>
            <li>container_2_{self.timestamp}.png - Third flight container</li>
        </ul>
    </div>
</body>
</html>
        """
        
        return report


async def main():
    """Test the visual validator"""
    import glob
    
    # Find a test HTML file
    html_files = glob.glob('raw_html_extreme_*.html')
    if not html_files:
        print("No test HTML files found")
        return
        
    test_file = html_files[0]  # Use first file
    print(f"Testing with: {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    validator = FlightVisualValidator(html_content)
    report_path = await validator.validate()
    
    print(f"\nValidation complete! Open the report:")
    print(f"open {report_path}")


if __name__ == "__main__":
    asyncio.run(main())