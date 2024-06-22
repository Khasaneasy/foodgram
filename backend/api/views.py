import base64
from http import HTTPStatus
import os
import shortuuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from shortener.models import Url

from .downcart import create_pdf
from .filters import IngredientFilter, RecipeFilter
from .mixins import ListRetrieveModelMixin
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnlyPermission
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          RecipeSerializer, TagSerializer)
from users.models import Subscribe

User = get_user_model()


class ProfileUserViewSet(UserViewSet):
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return (permissions.IsAuthenticatedOrReadOnly(), )
        return super().get_permissions()

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            avatar_base64 = request.data.get('avatar')
            if avatar_base64:
                avatar_base64 = avatar_base64.split(',')[1]
                avatar_data = base64.b64decode(avatar_base64)
                avatar_file = ContentFile(
                    avatar_data,
                    name=f'avatar{user.id}.png'
                )
                if user.avatar:
                    os.remove(user.avatar.path)
                user.avatar.save(f'avatar{user.id}.png', avatar_file)
                user.save()
                return Response(
                    AvatarSerializer(user, context={'request': request}).data
                )
            return Response(
                {'errors': 'Аватар не предоставлен'},
                status=HTTPStatus.BAD_REQUEST
            )
        if user.avatar:
            os.remove(user.avatar.path)
            user.avatar = None
            user.save()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response({'errors': 'У Вас нет аватара'},
                        status=HTTPStatus.BAD_REQUEST)

    @action(['POST'], detail=True, serializer_class=SubscribeSerializer)
    def subscribe(self, request, id=None):
        user = self.get_object()
        serializer = self.get_serializer(data={
            'follower': request.user.id,
            'following': user.id,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        follower = request.user
        following = get_object_or_404(User, id=id)
        subscription = Subscribe.objects.filter(
            follower=follower, following=following
        ).first()
        if subscription:
            subscription.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            data={'errors': 'Вы еще не подписаны на этого пользователя'},
            status=HTTPStatus.BAD_REQUEST
        )

    @action(['get'],
            detail=False,
            permission_classes=(IsAuthenticatedOrReadOnly,))
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        subscriptions = Subscribe.objects.filter(follower=user)
        paginator = PageLimitPagination()
        page = paginator.paginate_queryset(subscriptions, request)
        serializer = SubscribeSerializer(
            page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)


class TagViewSet(ListRetrieveModelMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class IngredientViewSet(ListRetrieveModelMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    pagination_class = PageLimitPagination
    permission_classes = (
        IsAuthorOrReadOnlyPermission,
        permissions.IsAuthenticatedOrReadOnly,
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_recipe(self, request, model, serializer, pk=None):
        user = self.request.user
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            error_status = (
                HTTPStatus.NOT_FOUND
                if model == ShoppingCart
                else HTTPStatus.BAD_REQUEST
            )
            return Response(
                status=error_status,
                data={'errors': 'Указанного рецепта не существует'}
            )

        serializer = serializer(data={'user': user.id, 'recipe': recipe.id},
                                context={'request': request})

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)
        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)

    def remove_recipe(self, request, model, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        instance = model.objects.filter(recipe=recipe, user=user)
        if instance.exists():
            instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        model_name = 'список покупок' if model == ShoppingCart else 'избранное'
        return Response(
            status=HTTPStatus.BAD_REQUEST,
            data={f'errors: Рецепт не был добавлен в {model_name}'},
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        context = {'request': request}
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = ShoppingCartSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response({'errors': 'Рецепт не найден в вашей корзине'},
                            status=HTTPStatus.BAD_REQUEST)

        return Response(status=HTTPStatus.NO_CONTENT)

    @action(['get'],
            permission_classes=(permissions.IsAuthenticated,),
            detail=False)
    def download_shopping_cart(self, request, *args, **kwargs):
        file = create_pdf(request.user)
        return file

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        context = {'request': request}
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = FavoriteSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response({'errors': 'Рецепт не найден в вашем избранном'},
                            status=HTTPStatus.BAD_REQUEST)

        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        long_url = request.build_absolute_uri(f'/recipes/{recipe.pk}/')
        short_id = shortuuid.uuid()[:6]
        short_url = Url.objects.create(long_url=long_url, short_id=short_id)
        short_link = request.build_absolute_uri(f'/s/{short_url.short_id}/')
        return Response({'short-link': short_link}, status=HTTPStatus.OK)
