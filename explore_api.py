"""
The Dyrt API'sini keşfetme scripti.

Bu script, The Dyrt web sitesinin API'sini keşfetmek ve API yapısını anlamak için kullanılır.
"""
import json
import logging
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def explore_dyrt_api():
    """
    The Dyrt API'sini keşfetme işlevi.
    """
    logger.info("The Dyrt API'sini keşfetmeye başlıyorum...")
    
    # Farklı API endpoint'leri denemesi
    api_versions = ["v4", "v5", "v6"]
    endpoint_templates = [
        "/search",
        "/search/campgrounds",
        "/campgrounds/search",
        "/campgrounds"
    ]
    
    # Base URL
    base_url_template = "https://thedyrt.com/api/{}"
    
    # Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://thedyrt.com/search",
    }
    
    # Create a client
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        for version in api_versions:
            base_url = base_url_template.format(version)
            
            for endpoint in endpoint_templates:
                url = f"{base_url}{endpoint}"
                
                param_sets = [
                    {
                        "bounds[north]": 49.0,
                        "bounds[east]": -66.0,
                        "bounds[south]": 24.0,
                        "bounds[west]": -125.0,
                        "limit": 10,
                    },
                    {
                        "bounds": "24.0,-125.0,49.0,-66.0",
                        "per_page": 10,
                        "page": 1
                    }
                ]
                
                for i, params in enumerate(param_sets):
                    try:
                        logger.info(f"Deneniyor: {url} (parametre seti {i+1})")
                        response = await client.get(url, params=params)
                        
                        if response.status_code == 200:
                            logger.info(f"Başarılı! URL: {url}")
                            logger.info(f"Parametreler: {params}")
                            
                            try:
                                json_data = response.json()
                                
                                logger.info(f"Yanıt tipi: {type(json_data)}")
                                
                                if isinstance(json_data, dict):
                                    logger.info(f"Yanıt anahtarları: {json_data.keys()}")
                                
                                logger.info(f"Yanıt örneği: {str(json_data)[:100]}...")
                                
                                with open(f"api_response_{version}_{endpoint.replace('/', '_')}.json", "w") as f:
                                    json.dump(json_data, f, indent=2)
                                    
                                logger.info(f"Yanıt dosyaya kaydedildi: api_response_{version}_{endpoint.replace('/', '_')}.json")
                                
                            except json.JSONDecodeError:
                                logger.warning("Yanıt JSON formatında değil.")
                        else:
                            logger.warning(f"Başarısız: {url}, Durum Kodu: {response.status_code}")
                    
                    except httpx.RequestError as e:
                        logger.error(f"İstek hatası: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(explore_dyrt_api())
