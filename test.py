from requests.sessions import Session

s = Session()
s.headers.update({'User-Agent': f'OAuth backman/1.0.0 (contact: ponbac@student.chalmers.se)'})
resp = s.post('http://127.0.0.1:8000/auth/test', data={'code': 'test-code', 'test': 'www.bonka.com'})

print(resp.json())
if resp.status_code == 200:
    print(resp.json())