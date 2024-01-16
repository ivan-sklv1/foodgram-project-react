from djoser.views import UserViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    RecipeListSerializer, RecipeCreateUpdateSerializer, TagSerializer, RecipeIngredientSerializer,
)
from recipes.models import Recipe, Tag, RecipeIngredient


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class CustomUserViewSet(UserViewSet):
    """API для пользователей."""


class RecipeViewSet(ReadOnlyModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch',]
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly,)
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ModelViewSet):
    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
