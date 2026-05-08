from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AISessionViewSet

app_name = "ai_tutor"

router = DefaultRouter()
# Provide explicit basenames and map 'ask' logically if you want, 
# but generic POST to /sessions/ works per the plan.
# I will map POST /ask/ to the viewset's create method explicitly to match the API design
# and GET /history/ to list.

# Note: The plan specified:
# POST /api/v1/tutor/ask/ (Create)
# GET /api/v1/tutor/history/ (List)
# GET /api/v1/tutor/history/{id}/ (Retrieve)

urlpatterns = [
    path('ask/', AISessionViewSet.as_view({'post': 'create'}), name='ask'),
    path('history/', AISessionViewSet.as_view({'get': 'list'}), name='history_list'),
    path('history/<uuid:pk>/', AISessionViewSet.as_view({'get': 'retrieve'}), name='history_detail'),
]
