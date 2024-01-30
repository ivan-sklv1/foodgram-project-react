from django.conf.urls import url
from django.urls import include
from rest_framework.routers import DefaultRouter

from api.views import (
    RecipeViewSet, CustomUserViewSet, TagViewSet, IngredientViewSet
)


router_v1 = DefaultRouter()
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'users', CustomUserViewSet, basename='users')


urlpatterns = [
    url(r'', include(router_v1.urls)),
    url('', include('djoser.urls')),
    url(r'^auth/', include('djoser.urls.authtoken')),
]
