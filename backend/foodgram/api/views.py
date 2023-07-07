from rest_framework import viewsets
from djoser.views import UserViewSet

from recipes.models import Ingredient, Tag, Recipe
from .pagination import CustomUsersPagination
from .serializers import IngredientSerializer, TagSerializer, UsersSerializer, RecipeSerializer
from .permissions import IsAdminOrReadOnly
from users.models import User


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = CustomUsersPagination


class RecipeViewSet(UserViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
