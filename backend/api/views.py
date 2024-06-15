import base64
import os
import shortuuid

from shortener.models import Url
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Subscribe

from .downcart import create_pdf
from .filters import RecipeFilter
from .mixins import ListRetrieveModelMixin
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnlyPermission
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeCreateSerializer, ShoppingCartSerializer,
                          SubscribeSerializer, TagSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
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
            else:
                return Response(
                    {'errors': 'Аватар не предоставлен'},
                    status=400
                )
        elif request.method == 'DELETE':
            if user.avatar:
                os.remove(user.avatar.path)
                user.avatar = None
                user.save()
                return Response(status=204)
            else:
                return Response({'errors': 'У вас нет аватара'}, status=400)

    @action(['POST'], detail=True, serializer_class=SubscribeSerializer)
    def subscribe(self, request, id=None):
        user = self.get_object()
        if request.user == user:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription, created = Subscribe.objects.get_or_create(
            follower=request.user, following=user
        )

        if created:
            serializer = SubscribeSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'errors': 'Вы уже подписаны'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        follower = request.user
        following = get_object_or_404(User, id=id)

        subscription = Subscribe.objects.filter(
            follower=follower,
            following=following,
        ).first()

        if subscription:
            subscription.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT,
            )

        error_message = (
            'Нельзя подписаться на себя'
            if follower.id == following.id
            else 'Вы уже подписаны'
        )
        return Response(
            data={'errors': error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(['get'],
            detail=False,
            permission_classes=(IsAuthenticatedOrReadOnly,))
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        subscriptions = Subscribe.objects.filter(follower=user)
        paginator = PageLimitPagination()
        paginated_subscriptions = paginator.paginate_queryset(
            subscriptions,
            request
        )
        if paginated_subscriptions is not None:
            serializer = SubscribeSerializer(
                paginated_subscriptions,
                many=True, context={'request': request}
            )
            return paginator.get_paginated_response(serializer.data)
        serializer = SubscribeSerializer(
            subscriptions, many=True, context={'request': request}
        )
        return Response(serializer.data)


class TagViewSet(ListRetrieveModelMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class IngredientViewSet(ListRetrieveModelMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__startswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    pagination_class = PageLimitPagination
    permission_classes = (IsAuthorOrReadOnlyPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_recipe(self, request, model, pk=None):

        user = request.user
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            error_status = (
                status.HTTP_404_NOT_FOUND
                if model == ShoppingCart
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(
                status=error_status,
                data={'errors': 'Указанного рецепта не существует'}
            )
        if model.objects.filter(recipe=recipe, user=user).exists():
            model_name = 'список покупок' if model == ShoppingCart else \
                'избранное'
            return Response(
                {'errors': f'Рецепт уже добавлен в {model_name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj = model.objects.create(
            recipe=recipe,
            user=user,
        )
        if model == ShoppingCart:
            serializer = ShoppingCartSerializer(obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        image = base64.b64encode(recipe.image.read()).decode('utf-8')
        response_data = {
            'id': recipe.id,
            'name': recipe.name,
            'cooking_time': recipe.cooking_time,
            'image': image,
        }
        return Response(data=response_data, status=status.HTTP_201_CREATED)

    def remove_recipe(self, request, model, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        instance = model.objects.filter(recipe=recipe, user=user)
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        model_name = 'список покупок' if model == ShoppingCart else 'избранное'
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={f'errors: Рецепт не был добавлен в {model_name}'},
        )

    @action(methods=['POST'],
            detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        return self.add_recipe(request, ShoppingCart, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.remove_recipe(request, ShoppingCart, pk)

    @action(['get'],
            permission_classes=(permissions.IsAuthenticated,),
            detail=False)
    def download_shopping_cart(self, request, *args, **kwargs):
        file = create_pdf(request.user)
        return file

    @action(methods=['POST'],
            detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        return self.add_recipe(request, Favorite, pk)

    @favorite.mapping.delete
    def del_favorite(self, request, pk=None):
        return self.remove_recipe(request, Favorite, pk)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        long_url = request.build_absolute_uri(f'/recipes/{recipe.pk}/')
        short_id = shortuuid.uuid()[:6]
        short_url = Url.objects.create(long_url=long_url, short_id=short_id)
        short_link = request.build_absolute_uri(f'/s/{short_url.short_id}/')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class SubscribeViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Subscribe.objects.filter(follower=self.request.user)
