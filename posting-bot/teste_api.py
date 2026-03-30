import os, requests
from dotenv import load_dotenv

load_dotenv('../.env')

token = os.getenv('META_ACCESS_TOKEN')
account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')

print('Token inicio:', token[:30] if token else 'VAZIO')
print('Account ID:', account_id)

r = requests.post(
    f'https://graph.facebook.com/v19.0/{account_id}/media',
    params={
        'image_url': 'https://mejulga.com.br/drajulga-post.jpg',
        'caption': 'teste',
        'access_token': token
    }
)
print('Resposta completa:', r.json())