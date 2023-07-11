from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Ingredient, Tag, Recipe
from .pagination import CustomUsersPagination
from .serializers import (IngredientSerializer, TagSerializer, UsersSerializer, RecipeSerializer,
                          SubscribeAuthorSerializer, SetPasswordSerializer, SubscriptionsSerializer)
from .permissions import IsAdminOrReadOnly
from users.models import User, Subscription


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

    @action(detail=False, methods=['get'], permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(subscriber__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['id'])

        if request.method == 'POST':
            if self.request.user == author:
                return Response({'detail': 'Невозмодно подписаться на самого себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscribeAuthorSerializer(author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Subscription, user=request.user, author=author).delete()
            return Response({'detail': 'Успешная отписка'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], permission_classes=(permissions.IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'}, status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(UserViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
