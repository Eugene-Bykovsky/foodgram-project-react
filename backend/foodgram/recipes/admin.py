from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Ingredient, Recipe, RecipeIngredientAmount,
                     ShoppingCart, Tag)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    list_filter = ('author', 'name', 'tags',)
    empty_value_display = '-пусто-'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorite_count=Count('in_favorites'))
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


admin.site.site_header = 'Административная страница проекта Foodgram'
admin.site.register(Tag)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
admin.site.register(RecipeIngredientAmount)
