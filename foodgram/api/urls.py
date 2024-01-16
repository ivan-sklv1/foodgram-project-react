from django.conf.urls import url
from django.urls import include
from rest_framework.routers import DefaultRouter

from api.views import RecipeViewSet, CustomUserViewSet, TagViewSet, IngredientViewSet


router_v1 = DefaultRouter()
router_v1.register(r'users', CustomUserViewSet, basename='users')
router_v1.register(r'tags', TagViewSet)
router_v1.register(r'recipes', RecipeViewSet)
router_v1.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    url(r'^auth/', include('djoser.urls.authtoken')),
    url('', include('djoser.urls')),
    url(r'', include(router_v1.urls)),
]
