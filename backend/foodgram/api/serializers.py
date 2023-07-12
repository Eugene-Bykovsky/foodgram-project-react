import base64

from rest_framework import serializers
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.fields import SerializerMethodField, ReadOnlyField
from django.core.files.base import ContentFile

from recipes.models import Ingredient, Tag, Recipe, RecipeIngredientAmount, ShoppingCart, Favorite
from users.models import User, Subscription


# RECIPES
class IngredientSerializer(serializers.ModelSerializer):
    """Стандартный сериализатор для ингридиентов"""

    class Meta:
        model = Ingredient
        fields = 'id', 'name', 'measurement_unit'


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов(кастомный)"""
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
        if not self.context.get('request').user.is_anonymous:
            user = self.context.get('request').user
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if not self.context.get('request').user.is_anonymous:
            user = self.context.get('request').user
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'name', 'image', 'description', 'ingredients', 'cooking_time', 'pub_date',
                  'is_favorited', 'is_in_shopping_cart',)


class FavoriteSerializer(serializers.ModelSerializer):
    """[POST, DEL]Сериализатор для Избранного (добавление и удаление рецептов) """

    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'


class ShoppingCartSerializer(FavoriteSerializer):
    """[POST, DEL]Сериализатор для Списка покупок (добавление и удаление рецептов) """


# USERS
class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователей(наследуется от djoser)"""

    class Meta:
        model = User
        fields = 'id', 'email', 'username', 'first_name', 'last_name', 'password'


class UsersSerializer(UserSerializer):
    """Сериализатор для пользователей(наследуется от djoser)"""
    is_subscribed = SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Subscription.objects.filter(user=user, author=obj).exists()

    class Meta:
        model = User
        fields = 'id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed'


class SetPasswordSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления пароля(кастомный)"""
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неверный пароль.'}
            )
        if validated_data['current_password'] == validated_data['new_password']:
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль не должен совпадать с текущим.'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


# SUBSCRIPTIONS #
class SubscriptionsSerializer(UsersSerializer):
    """[GET] Сериализатор возвращает пользователей, на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.(наследуется от UsersSerializer)"""
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = User
        fields = 'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count'

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
        fields = 'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count'

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Subscription.objects.filter(user=user, author=obj).exists()

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
