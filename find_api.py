"""
The Dyrt web sitesinin gerçek API uç noktasını bulmak için basit bir script.
"""
import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def find_actual_api():
    """
    The Dyrt web sitesinin gerçek API yapısını keşfetmek için.
    """
    # Tarayıcı gibi davranmak için headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://thedyrt.com/search",
        "Origin": "https://thedyrt.com",
        "Connection": "keep-alive",
    }
    
    # Tarayıcıda tespit edilen gerçek API endpoints'lerini deneyelim
    endpoints = [
        "/api/search/results",
        "/api/v4/search/campgrounds"
    ]
    
    # Test etmek için yaklaşık US bound'ları
    bounds = "24.0,-125.0,49.0,-66.0"
    
    for endpoint in endpoints:
        url = f"https://thedyrt.com{endpoint}"
        
        # Tarayıcının gerçek istek parametreleri
        params = {
            "bounds": bounds,
            "sort": "recommended",
            "page": 1,
            "per_page": 50
        }
        
        try:
            logger.info(f"Testing endpoint: {url}")
            response = requests.get(url, headers=headers, params=params)
            
            # HTTP durumunu kontrol et
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"Success! Found working endpoint: {url}")
                
                # Yanıtı JSON olarak ayrıştır
                data = response.json()
                
                # Yanıt yapısını inceleyerek içindeki kampları bul
                if isinstance(data, dict):
                    logger.info(f"Response is a dictionary with keys: {data.keys()}")
                    
                    # Yanıtı bir dosyaya kaydet
                    with open(f"api_response_{endpoint.replace('/', '_')}.json", "w") as f:
                        json.dump(data, f, indent=2)
                    
                    # Kamp alanlarını bulmaya çalış
                    if "results" in data and "campgrounds" in data["results"]:
                        campgrounds = data["results"]["campgrounds"]
                        logger.info(f"Found {len(campgrounds)} campgrounds in results.campgrounds")
                        
                        # İlk kampı göster
                        if campgrounds:
                            logger.info(f"First campground: {campgrounds[0]}")
                    elif "campgrounds" in data:
                        campgrounds = data["campgrounds"]
                        logger.info(f"Found {len(campgrounds)} campgrounds directly in campgrounds")
                        
                        # İlk kampı göster
                        if campgrounds:
                            logger.info(f"First campground: {campgrounds[0]}")
                elif isinstance(data, list):
                    logger.info(f"Response is a list with {len(data)} items")
                
                logger.info(f"Response saved to api_response_{endpoint.replace('/', '_')}.json")
            else:
                logger.warning(f"Failed with status code {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error testing endpoint {url}: {e}")

if __name__ == "__main__":
    find_actual_api()
