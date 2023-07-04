from rest_framework import viewsets

from recipes.models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer
from .permissions import IsAdminOrReadOnly
from .pagination import LimitPagination


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitPagination


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
