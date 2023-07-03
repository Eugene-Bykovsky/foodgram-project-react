from rest_framework import viewsets

from recipes.models import Ingredient
from .serializers import IngredientSerializer
from .permissions import IsAdminOrReadOnly
from .pagination import LimitPagination


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitPagination
