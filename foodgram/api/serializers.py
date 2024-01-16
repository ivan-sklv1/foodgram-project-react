#!-*-coding:utf-8-*-
import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, Tag, RecipeIngredient


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomRegisterSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        )

#    def get_is_subscribed(self, obj):
#        request = self.context.get('request')
#        if request and request.user.is_authenticated:
#            return Follow.objects.filter(user=request.user, author=obj).exists()
#        return False


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте"""
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.IntegerField(
        source='ingredient.measurement_unit'
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    """Создание ингредиента в рецепте."""
    recipe = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'recipe', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Получение списка рецептов."""
    ingredients = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField()
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    def get_ingredients(self, obj):
        """Возвращает отдельный сериализатор."""
        return RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data

    class Meta:
        model = Recipe
        fields = (
            'title',
            'ingredients',
            'is_favorite',
            'author',
            'description'
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание или изменение рецепта."""
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientCreateInRecipeSerializer(
        many=True,
        required=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        source='tags',
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    image = Base64ImageField(required=True, allow_null=True)

    def validate_ingredients(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Должен быть хотя бы один ингредиент'
            )
        return value

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        create_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(create_ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Изменение рецепта."""
        ingredient = validated_data.pop('ingredients')
        if ingredient is not None:
            instance.ingredients.clear()

            create_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredient
            ]
            RecipeIngredient.objects.bulk_create(create_ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['tags'] = TagSerializer(instance.tags.all(), many=True).data
        data['ingredients'] = RecipeIngredientSerializer(
            instance.ingredients.all(), many=True
        ).data
        return data
#    def to_representation(self, obj):
#        """Возвращает представление в том же виде, что и GET-запрос."""
#        self.fields.pop('ingredients')
#        representation = super().to_representation(obj)
#        representation['ingredients'] = RecipeIngredientSerializer(
#            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
#        ).data
#        return representation

    class Meta:
        model = Recipe
        fields = (
            'title',
            'ingredients',
            'description',
            'id',
            'cooking_time',
            'tags',
            'image'
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
