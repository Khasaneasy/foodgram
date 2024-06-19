from drf_base64.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.relations import PrimaryKeyRelatedField
from djoser.serializers import UserSerializer
from rest_framework import serializers

from .constants import COOK_TIME, COOKING_QUANITY, INGREDIENT_QUANITY
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscribe


User = get_user_model()


class ProfileUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.following.filter(follower=user).exists()
        return False

    def validate(self, data):
        if 'first_name' not in data or 'last_name' not in data:
            raise serializers.ValidationError(
                {'first_name': 'Это поле обязательно.',
                 'last_name': 'Это поле обязательно.'}
            )
        return data


class AvatarSerializer(ProfileUserSerializer):
    class Meta:
        model = User
        fields = ('avatar',)


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ('follower', 'following')

    def validate(self, data):
        follower = data['follower']
        following = data['following']
        if follower == following:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return data

    def create(self, validated_data):
        follower = validated_data['follower']
        following = validated_data['following']
        subscription, created = Subscribe.objects.get_or_create(
            follower=follower, following=following
        )
        if not created:
            raise serializers.ValidationError('Вы уже подписаны')
        return subscription

    def to_representation(self, instance):
        return SubscriberSerializer(
            instance.following,
            context=self.context
        ).data


class SubscriberSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='following.id'
    )
    email = serializers.ReadOnlyField(
        source='following.email'
    )
    username = serializers.ReadOnlyField(
        source='following.username'
    )
    first_name = serializers.ReadOnlyField(
        source='following.first_name'
    )
    last_name = serializers.ReadOnlyField(
        source='following.last_name'
    )
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscribe.objects.filter(
            follower=user,
            following=obj.following
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.following)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeDetailSerializer(
            queryset,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.following).count()

    def get_avatar(self, obj):
        if obj.following.avatar:
            return obj.following.avatar.url
        return None


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug'
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        required=True
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = ProfileUserSerializer(
        required=False,
        read_only=True
    )
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True
    )

    is_favorited = serializers.BooleanField(
        read_only=True,
        default=False
    )
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return request.user.is_authenticated and obj.favorites.filter(
            user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.shopping_cart.filter(user=request.user).exists())


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = ProfileUserSerializer(required=False, read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True,
        allow_empty=False,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    @transaction.atomic
    def create_bulk_ing_tag(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    amount=ing['amount'],
                    ingredient=Ingredient.objects.get(id=ing['id']),
                ) for ing in ingredients
            ]
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags', [])

        if not tags:
            raise serializers.ValidationError('Добавьте тег')
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингредиент')

        tags_set = set(tags)
        if len(tags) != len(tags_set):
            raise serializers.ValidationError('Теги не должны дублироваться.')

        seen_ingredients = set()
        existing_ids = set(Ingredient.objects.values_list('id', flat=True))

        for ingredient_data in ingredients:
            ing_id = ingredient_data.get('id')
            if ing_id not in existing_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ing_id} не существует.'
                )
            if ing_id in seen_ingredients:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ing_id} добавлен более одного раза.'
                )
            seen_ingredients.add(ing_id)

            amount = ingredient_data.get('amount')
            try:
                amount = int(amount)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть числом.'
                )

            if amount <= INGREDIENT_QUANITY:
                raise serializers.ValidationError(
                    f'Количество ингредиента'
                    f'должно быть больше {INGREDIENT_QUANITY}.'
                )

        if data.get('cooking_time', COOKING_QUANITY) < COOK_TIME:
            raise serializers.ValidationError(
                f'Время готовки должно быть больше {COOK_TIME} минуты.'
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self.create_bulk_ing_tag(recipe, ingredients_data)
        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)

        instance.tags.set(tags_data)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_bulk_ing_tag(instance, ingredients_data)

        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return RecipeDetailSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return RecipeDetailSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class RecipeDetailSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
