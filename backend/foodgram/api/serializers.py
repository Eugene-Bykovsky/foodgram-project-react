import base64
import re

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredientAmount, ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.fields import (CharField, IntegerField, ReadOnlyField,
                                   SerializerMethodField)
from rest_framework.relations import PrimaryKeyRelatedField
from users.models import Subscription, User


# RECIPES
class IngredientSerializer(serializers.ModelSerializer):
    """Стандартный сериализатор для ингридиентов"""

    class Meta:
        model = Ingredient
        fields = 'id', 'name', 'measurement_unit'


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов при создании рецепта."""
    id = IntegerField()

    class Meta:
        model = RecipeIngredientAmount
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Стандартный сериализатор для тегов"""

    class Meta:
        model = Tag
        fields = 'id', 'name', 'color', 'slug'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингридиентов в рецепте"""
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredientAmount
        fields = 'id', 'name', 'measurement_unit', 'amount'


class Base64ImageField(serializers.ImageField):
    """Сериализатор для кодирования картинок(из теории)"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UsersSerializer(UserSerializer):
    """Сериализатор для пользователей(наследуется от djoser)"""
    is_subscribed = SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return (user.is_authenticated
                and Subscription.objects.filter(user=user,
                                                author=obj).exists())

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов(кастомный)"""
    author = UsersSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    @staticmethod
    def get_ingredients(obj):
        ingredients = RecipeIngredientAmount.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'name', 'image', 'text',
                  'ingredients', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart',)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    ingredients = IngredientCreateSerializer(many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                  many=True)
    image = Base64ImageField()
    name = CharField(max_length=200)
    cooking_time = IntegerField()
    author = UserSerializer(read_only=True)

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовения не может быть меньше 1 минуты')
        return value

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags',
                  'image', 'name', 'text',
                  'cooking_time', 'author')


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """[POST, DEL]Сериализатор для Избранного (добавление и удаление рец.) """

    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeFavoriteSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingCartSerializer(FavoriteSerializer):
    """[POST, DEL]Сериализатор для Списка покупок (добавление и удаление) """


# USERS
class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователей(наследуется от djoser)"""
    username = serializers.CharField(max_length=150)

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                "Username should only contain letters, digits, "
                "and @/./+/-/_ characters."
            )
        return value

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name',
                  'password')
        extra_kwargs = {'password': {'write_only': True}}


class SetPasswordSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления пароля(кастомный)"""
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неверный пароль.'}
            )
        if (validated_data['current_password']
                == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль не должен совпадать с текущим.'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


# SUBSCRIPTIONS #
class SubscriptionsSerializer(UsersSerializer):
    """[GET] Сериализатор возвращает пользователей,
    на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.(наследуется от UsersSerializer)"""
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    """[POST, DELETE] Сериализатор для подписки и отписки(кастомный)."""
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return (user.is_authenticated
                and Subscription.objects.filter(user=user,
                                                author=obj).exists())

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

# SUBSCRIPTIONS #
