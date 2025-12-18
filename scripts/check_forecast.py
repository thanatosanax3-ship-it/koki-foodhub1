import urllib.request, urllib.error
url = 'https://koki-foodhub-app.onrender.com/forecast/'
try:
    r = urllib.request.urlopen(url, timeout=10)
    print('Status', r.status)
    body = r.read().decode('utf-8', 'replace')
    print('Body head:', body[:1000])
except urllib.error.HTTPError as e:
    print('HTTPError', e.code)
    print('Body:', e.read().decode('utf-8', 'replace')[:2000])
except Exception as e:
    print('Error', e)
