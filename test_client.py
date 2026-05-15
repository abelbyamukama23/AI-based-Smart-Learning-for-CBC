import os
os.environ["DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbc_backend.settings")

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
u = User.objects.first()

if not u:
    print("No users found")
    exit()

c = Client()
c.force_login(u)

print("Sending request to /api/v1/tutor/ask/")
try:
    response = c.post('/api/v1/tutor/ask/', {'query': 'What is photosynthesis?', 'mode': 'default'}, content_type='application/json')
    print("Status code:", response.status_code)
    print("Headers:", response.headers)
    if hasattr(response, 'streaming_content'):
        for chunk in response.streaming_content:
            print(chunk)
    else:
        print("Content:", response.content)
except Exception as e:
    import traceback
    traceback.print_exc()
