import base64
from rest_framework import serializers
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.fields import SerializerMethodField, ReadOnlyField
from django.core.files.base import ContentFile

from recipes.models import Ingredient, Tag, Recipe, RecipeIngredientAmount, ShoppingCart, Favorite
from users.models import User, Subscription


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = 'id', 'name', 'measurement_unit'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = 'id', 'name', 'color', 'slug'


class CreateUserSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'password',)


class UsersSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredientAmount
        fields = ('id', 'name',
                  'measurement_unit',
                  'amount',)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
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
            return Favorite.objects.filter(
                user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if not self.context.get('request').user.is_anonymous:
            user = self.context.get('request').user
            return ShoppingCart.objects.filter(
                user=user, recipe=obj).exists()
        return False

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'name', 'image',
                  'description', 'ingredients',
                  'cooking_time', 'pub_date',
                  'is_favorited', 'is_in_shopping_cart',)
