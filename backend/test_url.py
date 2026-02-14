import urllib.request
import urllib.error
import urllib.parse
import sys

BASE_URL = "http://localhost:8000/api/v1/admin/import-jobs/template/"

def test_url(params=None):
    url = BASE_URL
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    print(f"Testing URL: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            print(f"Status Code: {response.getcode()}")
            print(f"Content: {response.read()[:200]}")
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")
        print(f"Content: {e.read()[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("--- No Params ---")
    test_url()
    
    print("\n--- Dummy Params ---")
    test_url({'foo': 'bar'})

    print("\n--- Custom Param Name (fmt) ---")
    test_url({'fmt': 'xlsx', 'include_examples': 'true'})
