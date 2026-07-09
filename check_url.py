import urllib.request
import re

try:
    html = urllib.request.urlopen('https://aegis-flax-nine.vercel.app/').read().decode('utf-8')
    js_url = re.search(r'/assets/index-[^.]+\.js', html).group(0)
    js = urllib.request.urlopen('https://aegis-flax-nine.vercel.app' + js_url).read().decode('utf-8')
    
    # Try to find common API base URLs baked into the compiled JS
    # e.g., http://172.18.223.247:8000/api
    urls = set(re.findall(r'https?://[a-zA-Z0-9.\-:]+/api', js))
    
    print("API URLs found in compiled JS:", urls)
except Exception as e:
    print("Error:", e)
