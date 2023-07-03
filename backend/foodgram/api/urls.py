from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet

app_name = 'api'

router = DefaultRouter()

router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = (
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
)
