import requests

def test_check():
    x = requests.get('http://127.0.0.1:8081/upload/new')
    newjson = x.json()
    for y in newjson:
        print(y)

test_check()