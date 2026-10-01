import os
from dotenv import load_dotenv

# Load .env file explicitly since we are running a standalone script
load_dotenv()

def get_xano_api_url():
    configured_url = os.getenv("XANO_API_URL", "").strip().rstrip("/")
    if configured_url:
        return configured_url
    return "https://x8ki-letl-twmt.n7.xano.io/api:9gPvpDtO"

def get_xano_services_url():
    configured_url = os.getenv("XANO_SERVICES_URL", "").strip().rstrip("/")
    if configured_url:
        return configured_url
    return get_xano_api_url()

def test_urls():
    api_url = get_xano_api_url()
    services_url = get_xano_services_url()
    
    print(f"API URL: {api_url}")
    print(f"Services URL: {services_url}")
    
    if api_url != services_url:
        print("SUCCESS: URLs are different.")
    else:
        print("FAILURE: URLs are identical.")

if __name__ == "__main__":
    test_urls()
