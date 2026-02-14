
import requests

URLS_TO_TEST = [
    "https://vital.b-cdn.net/01VTL-GKO7010/P0001VTL-GKO70101.png",
    "https://vital.b-cdn.net/01VTL-GKO7020/P0001VTL-GKO70201.png",
    "https://vital.b-cdn.net/01VTL-GKW7010/P0001VTL-GKW70101.png",
    "https://vital.b-cdn.net/01VTL-GKS7010/P0001VTL-GKS70101.png",
    "https://vital.b-cdn.net/01VTL-EKO7010/P0001VTL-EKO70101.png",
    "https://vital.b-cdn.net/01VTL-IKO7010/P0001VTL-IKO70101.png",
    "https://vital.b-cdn.net/01VTL-EST7010/P0001VTL-EST70101.png",
]

def test_urls():
    print(f"Testing {len(URLS_TO_TEST)} URLs...\n")
    print(f"{'Status':<8} | URL")
    print("-" * 80)
    
    for url in URLS_TO_TEST:
        try:
            response = requests.head(url, timeout=5)
            # If HEAD fails (some CDNs block it), try GET
            if response.status_code >= 400:
                response = requests.get(url, stream=True, timeout=5)
                response.close()
            
            status = response.status_code
            print(f"{status:<8} | {url}")
        except Exception as e:
            print(f"{'ERROR':<8} | {url} ({str(e)})")

if __name__ == "__main__":
    test_urls()
