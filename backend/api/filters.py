from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited',
                  'is_in_shopping_cart',)

    def filter_is_favorited(self, queryset, name, value):
        return queryset.filter(
            favorites__user=self.request.user
        ) if value and self.request.user.is_authenticated else queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return queryset.filter(
            shopping_carts__user=self.request.user
        ) if value and self.request.user.is_authenticated else queryset


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']
