from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredientAmount, ShoppingCart, Tag)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import Subscription, User

from .filters import IngredientFilter, RecipesFilter
from .pagination import CustomUsersPagination
from .permissions import IsAdminOrAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          SetPasswordSerializer, SubscribeSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UsersSerializer)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = CustomUsersPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(subscriber__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(pages, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['id'])

        if request.method == 'POST':
            if self.request.user == author:
                return Response({'detail': 'Невозмодно подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscribeSerializer(author, data=request.data,
                                             context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(Subscription, user=request.user,
                          author=author).delete()
        return Response({'detail': 'Успешная отписка'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'],
            permission_classes=(permissions.IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)


def recipe_add_or_del_method(request, pk, model):
    recipe = get_object_or_404(Recipe, id=pk)
    if request.method == 'POST':
        _, created = model.objects.get_or_create(
            user=request.user, recipe=recipe)
        if created:
            serializer = RecipeShortSerializer(recipe)
            return Response(
                {'detail': f'Рецепт добавлен в {model.__name__}!',
                 'data': serializer.data},
                status=status.HTTP_201_CREATED)
        return Response(
            {'message': f'Рецепт уже находится в {model.__name__}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    recipe = get_object_or_404(model, user=request.user, recipe=recipe)
    recipe.delete()
    return Response({'detail': f'Рецепт успешно удален из {model.__name__}'},
                    status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(UserViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    pagination_class = CustomUsersPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    serializer_class = RecipeCreateSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk=None):
        return recipe_add_or_del_method(request, pk, Favorite)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        return recipe_add_or_del_method(request, pk, ShoppingCart)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredientAmount.objects.filter(
            recipe__in_shopping_carts__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(
            total_amount=Sum('amount'))
        data = ingredients.values_list('ingredient__name',
                                       'ingredient__measurement_unit',
                                       'amount')
        shopping_cart = 'Список покупок:\n'
        for name, measure, amount in data:
            shopping_cart += f'- {name} в количестве: {amount} {measure},\n'
        response = HttpResponse(shopping_cart, content_type='text/plain')
        return response
