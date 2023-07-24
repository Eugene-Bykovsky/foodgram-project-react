from .serializers import RecipeShortSerializer
from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import status
from rest_framework.response import Response


def recipe_add_or_del_method(request, model, pk):
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


def check_subscribed(request, obj, model):
    if request and not request.user.is_anonymous:
        return model.objects.filter(
            user=request.user, author=obj).exists()
    return False
