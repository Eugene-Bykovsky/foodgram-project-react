from rest_framework import viewsets, status
from djoser.views import UserViewSet

from recipes.models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer, UsersSerializer
from .permissions import IsAdminOrReadOnly
from .pagination import LimitPagination
from users.models import User


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitPagination


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer

