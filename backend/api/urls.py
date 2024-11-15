from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (ProfileUserViewSet, IngredientViewSet,
                    RecipeViewSet, TagViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('users', ProfileUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
