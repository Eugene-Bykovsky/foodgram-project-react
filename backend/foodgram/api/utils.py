from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe
from users.models import Subscription


def recipe_add_or_del_method(request, model, pk, custom_serializer):
    recipe = get_object_or_404(Recipe, id=pk)
    if request.method == 'POST':
        _, created = model.objects.get_or_create(
            user=request.user, recipe=recipe)
        if created:
            serializer = custom_serializer(recipe)
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


def check_subscribed(request, obj):
    if request and not request.user.is_anonymous:
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()
    return False
