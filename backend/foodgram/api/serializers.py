from rest_framework import serializers
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.fields import SerializerMethodField, ReadOnlyField

from recipes.models import Ingredient, Tag, Recipe, RecipeIngredientAmount
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


class RecipeSerializer(serializers.ModelSerializer):
    ingredient = serializers.SerializerMethodField()
    tag = TagSerializer(many=True)

    @staticmethod
    def get_ingredient(obj):
        ingredient = RecipeIngredientAmount.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredient, many=True).data

    class Meta:
        model = Recipe
        fields = ('author', 'name', 'image',
                  'description', 'ingredient',
                  'tag', 'cooking_time', 'pub_date')
