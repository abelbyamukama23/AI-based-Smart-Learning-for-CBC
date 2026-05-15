from apps.ai_tutor.agent import run_tutor_agent_stream
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.first()

if not u:
    print("No users found")
    exit()

print("Starting stream...")
try:
    for chunk in run_tutor_agent_stream(
        user_id=str(u.id),
        query="What is photosynthesis?",
        context_lesson_id=None,
        history=[],
        image_b64=None,
        image_mime=None,
        mode="default"
    ):
        print("CHUNK:", chunk)
except Exception as e:
    import traceback
    traceback.print_exc()
