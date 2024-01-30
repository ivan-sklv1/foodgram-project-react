from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from api.serializers import (
    RecipeListSerializer, RecipeCreateUpdateSerializer, TagSerializer,
    FavoriteRecipeSerializer, IngredientSerializer,
    CustomUserSerializer, SubscribeSerializer
)
from users.models import User, Subscribe
from recipes.models import (
    Recipe, Tag, RecipeIngredient, Ingredient, ShoppingCart, FavoriteRecipe
)


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination
    http_method_names = ['get',]

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        """Метод для создания подписки."""

        user = self.request.user
        author = get_object_or_404(User, id=id)
        change_subscription_status = Subscribe.objects.filter(
            user=user.id,
            author=author.id
        )
        if request.method == 'POST':
            if user == author:
                return Response(
                    'Вы пытаетесь подписаться на себя!!',
                    status=status.HTTP_400_BAD_REQUEST
                )
            if change_subscription_status.exists():
                return Response(
                    f'Вы подписаны на {author}',
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscribe = Subscribe.objects.create(
                user=user,
                author=author
            )
            subscribe.save()
            return Response(
                f'Вы подписались на {author}',
                status=status.HTTP_201_CREATED
            )
        if change_subscription_status.exists():
            change_subscription_status.delete()
            return Response(
                f'Вы отписались от {author}',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            f'Вы не подписаны на {author}',
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me',
        url_name='me',
    )
    def me(self, request, *args, **kwargs):
        user = self.request.user
        serializer = CustomUserSerializer(
            user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated, ),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Метод для просмотра подписок."""

        queryset = User.objects.filter(follow__user=self.request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Метод для выбора сериализатора."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    @action(
        ("post", "delete"),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        """Метод для добавления в избранное."""

        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            if FavoriteRecipe.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    "Рецепт уже есть в избранном.",
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = FavoriteRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if not FavoriteRecipe.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    "Рецепта нет в избранном.",
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.filter(user=user, recipe=recipe).delete()
            return Response(
                "Рецепт успешно удалён из избранного.",
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        ("post", "delete"),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        """Метод для добавления в список покупок."""

        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': f'Повторно - \"{recipe.name}\" добавить нельзя,'
                               f'он уже есть в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = FavoriteRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            get_object_or_404(
                ShoppingCart, user=request.user, recipe=recipe
            ).delete()
            return Response(
                {"detail": "Рецепт успешно удален из списка покупок."},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': f'Рецепта \"{recipe.name}\" нет в списке покупок.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Метод для объединения ингредиентов в список для загрузки."""

        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Метод для загрузки списка ингредиентов."""

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_recipe__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')


class TagViewSet(ModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_class = (AllowAny,)
    http_method_names = ['get']


class IngredientViewSet(ModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_class = (IsAdminOrReadOnly)
    search_fields = ('^name')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    http_method_names = ['get']
