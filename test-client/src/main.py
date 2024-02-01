from base64 import b64decode, b64encode
import json

import httpx

with open('./src/steve.png', 'rb') as f:
    image_bytes = b64encode(f.read())
res = httpx.post('http://app:8080/2015-03-31/functions/function/invocations', data=json.dumps({
    'httpMethod': 'POST',
    'path': '/skinpacks',
    'body': {
        'skinpack': {
            'id': 'OneMoreSteve',
            'name': 'One More Steve',
            'translations': [
                {
                    'lang': 'en_US',
                    'text': 'One More Steve'
                },
                {
                    'lang': 'ja_JP',
                    'text': 'もう一人のスティーブ'
                }
            ]
        },
        'skins': [
            {
                'id': 'steve',
                'translations': [
                    {
                        'lang': 'en_US',
                        'text': 'Steve...?'
                    },
                    {
                        'lang': 'ja_JP',
                        'text': 'スティーブ...？'
                    }
                ],
                'image': image_bytes.decode('utf-8')
            }
        ]
    }
}))
if not ('statusCode' in res.json() and res.json()['statusCode'] == 200):
    print(res.json())
    raise Exception()
data = json.loads(res.json()['body'])

with open(f'./output/{data["name"]}', 'wb') as f:
    f.write(b64decode(data['content']))
