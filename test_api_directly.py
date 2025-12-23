import requests
import json

# Disable warnings
import urllib3
urllib3.disable_warnings()

def test_api():
    base = "https://www.nepalstock.com.np/api/nots"
    
    endpoints = {
        "top_gainers": f"{base}/topTen/topGainer",
        "top_losers": f"{base}/topTen/topLoser",
        "all_securities": f"{base}/securityDailyTradeStat/58",
        "companies": f"{base}/company",
        "market_summary": f"{base}/market-summary",
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Android; Mobile)',
        'Accept': 'application/json',
    }
    
    print("="*60)
    print("Testing NEPSE API Endpoints")
    print("="*60)
    
    for name, url in endpoints.items():
        print(f"\n📡 Testing: {name}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content Length: {len(response.text)} chars")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"✅ Got LIST with {len(data)} items")
                        if data:
                            print(f"First item keys: {list(data[0].keys())}")
                            # Show first item for analysis
                            print(f"Sample data: {json.dumps(data[0], indent=2)[:200]}...")
                    elif isinstance(data, dict):
                        print(f"✅ Got DICT with keys: {list(data.keys())}")
                        # Show a preview
                        print(f"Sample: {json.dumps(data, indent=2)[:200]}...")
                    else:
                        print(f"⚠️ Unexpected data type: {type(data)}")
                        print(f"First 500 chars: {response.text[:500]}")
                except json.JSONDecodeError:
                    print("❌ Response is not valid JSON")
                    print(f"First 500 chars: {response.text[:500]}")
            elif response.status_code == 404:
                print("❌ 404 - Endpoint not found")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print("\n" + "="*60)
    print("Testing website access...")
    
    # Test main website
    try:
        response = requests.get("https://www.nepalstock.com.np", verify=False, timeout=10)
        print(f"Website Status: {response.status_code}")
        
        # Check if it's the right website
        if "NEPSE" in response.text or "nepalstock" in response.text.lower():
            print("✅ Correct website detected")
            
            # Try to find API endpoints in page source
            import re
            api_patterns = re.findall(r'/api/nots/[a-zA-Z]+', response.text)
            if api_patterns:
                print(f"Found API patterns: {set(api_patterns[:10])}")
        else:
            print("⚠️ Website doesn't look like NEPSE")
            
    except Exception as e:
        print(f"❌ Website test failed: {e}")

if __name__ == "__main__":
    test_api()
