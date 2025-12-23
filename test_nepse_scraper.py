import logging
logging.basicConfig(level=logging.INFO)

try:
    from nepse_scraper import NepseScraper
    print("✅ nepse-scraper imported successfully")
    
    # Test the client
    client = NepseScraper(verify_ssl=False)
    print("✅ Client initialized")
    
    # Test getting data
    print("Testing get_today_price()...")
    data = client.get_today_price()
    print(f"Got data type: {type(data)}")
    
    if data:
        print(f"Got {len(data)} items")
        if isinstance(data, list) and len(data) > 0:
            print("\nSample item:")
            print(data[0])
            print(f"\nKeys: {list(data[0].keys())}")
    else:
        print("No data returned")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
