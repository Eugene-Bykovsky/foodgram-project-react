import re

from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField

from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredientAmount, ShoppingCart, Tag)
from users.models import User
from .fields import Base64ImageField
from .utils import check_subscribed


# RECIPES
class IngredientSerializer(serializers.ModelSerializer):
    """Стандартный сериализатор для ингридиентов"""

    class Meta:
        model = Ingredient
        fields = 'id', 'name', 'measurement_unit'


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов при создании рецепта."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredientAmount
        fields = 'id', 'amount'


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


class UsersSerializer(UserSerializer):
    """Сериализатор для пользователей(наследуется от djoser)"""
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return check_subscribed(request=self.context.get('request'), obj=obj)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов(кастомный)"""
    author = UsersSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True,
                                               source='recipes')
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        return (self.context.get('request')
                and not self.context.get('request').user.is_anonymous
                and self.context.get('request').user.favorites.filter(
                    recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        return (self.context.get('request')
                and not self.context.get('request').user.is_anonymous
                and self.context.get('request').user.shopping_carts.filter(
                    recipe=obj).exists())

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'name', 'image', 'text',
                  'ingredients', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart')


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователей(наследуется от djoser)"""
    username = serializers.CharField(max_length=150)

    @staticmethod
    def validate_username(value):
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                "Username should only contain letters, digits, "
                "and @/./+/-/_ characters."
            )
        return value

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name',
                  'password', 'id')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    ingredients = IngredientCreateSerializer(many=True)
    image = Base64ImageField(
        max_length=None,
        use_url=True)
    author = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    def validate(self, data):
        if Recipe.objects.exclude(pk=data['id']).filter(**data).exists():
            raise serializers.ValidationError('Данный рецепт уже добавлен!')
        return data

    def validate_ingredients(self, data):
        ingredients_list = []
        for ingredient in data:
            if ingredient.get('amount') == 0:
                raise serializers.ValidationError(
                    'Количество ингридиентов не может равняться 0!'
                )
            ingredients_list.append(ingredient.get('id'))
        # Пррверяем уникальность
        if len(set(ingredients_list)) != len(ingredients_list):
            raise serializers.ValidationError(
                'В рецепте не может быть двух одинаковых ингридиентов!'
            )
        return data

    @staticmethod
    def validate_cooking_time(value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовения не может быть меньше 1 минуты')
        return value

    class Meta:
        model = Recipe
        fields = '__all__'

    @staticmethod
    def save_ingredients(recipe, ingredients):
        RecipeIngredientAmount.objects.bulk_create(
            [RecipeIngredientAmount(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.save_ingredients(instance, ingredients)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeSerializer(instance, context=context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'


class FavoriteSerializer(serializers.ModelSerializer):
    """[POST, DEL]Сериализатор для Избранного (добавление и удаление рец.) """

    class Meta:
        model = Favorite
        fields = 'user', 'recipe'


class ShoppingCartSerializer(FavoriteSerializer):
    """[POST, DEL]Сериализатор для Списка покупок (добавление и удаление) """

    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart


# USERS

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

    class Meta:
        model = User
        fields = 'current_password', 'new_password'


# SUBSCRIPTIONS #
class SubscriptionsSerializer(UsersSerializer):
    """[GET] Сериализатор возвращает пользователей,
    на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.(наследуется от UsersSerializer)"""
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

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
        return check_subscribed(request=self.context.get('request'), obj=obj)

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data

# SUBSCRIPTIONS #
