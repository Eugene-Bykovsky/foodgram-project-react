from django.contrib import admin
from .models import Ingredient, Tag, Recipe, ShoppingCart, Favorite

admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
