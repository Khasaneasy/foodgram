from drf_base64.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

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


class CustomUserSerializer(UserSerializer):
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
        if not user or user.is_anonymous:
            return False
        return Subscribe.objects.filter(follower=user, following=obj.id)\
            .exists()


class AvatarSerializer(CustomUserSerializer):
    class Meta:
        model = User
        fields = ('avatar',)


class SubscribeSerializer(serializers.ModelSerializer):
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
        read_only_fields = (
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
    id = serializers.SerializerMethodField(
        source='ingredient.id'
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
        validators = [
            UniqueTogetherValidator(
                queryset=RecipeIngredient.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(
        required=False,
        read_only=True)
    tags = TagSerializer(
        many=True,
        read_only=True)
    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()
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
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_id(self, obj):
        return f'{obj.pk}'

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return [
            {
                'id': recipe_ingredient.ingredient.id,
                'name': recipe_ingredient.ingredient.name,
                'amount': recipe_ingredient.amount,
                'measurement_unit':
                recipe_ingredient.ingredient.measurement_unit,
            }
            for recipe_ingredient in recipe_ingredients
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj,
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj,
            ).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(required=False, read_only=True)
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
        ingredients = data.get('ingredients', [])
        tags = data.get('tags', [])

        if not tags:
            raise serializers.ValidationError('Добавьте тег')
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингрудиент')
        if len(tags) == 0:
            raise serializers.ValidationError(
                'Поле "tags" не должно быть пустым.'
            )
        existing_ids = set(Ingredient.objects.values_list(
            'id', flat=True)
        )
        for ingredient_data in ingredients:
            ing_id = ingredient_data.get('id')
            if ing_id not in existing_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ing_id} не существует.'
                )
            amount = ingredient_data.get('amount')
            try:
                amount = int(amount)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть числом.'
                )

            if amount <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0.'
                )

        if data.get('cooking_time', 0) < 1:
            raise serializers.ValidationError(
                'Время готовки должно быть больше 1 минуты.'
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags_data = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self.create_bulk_ing_tag(recipe, ingredients_data)
        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags_data = validated_data.pop('tags', [])
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        if tags_data:
            instance.tags.set(tags_data)
        if ingredients_data:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_bulk_ing_tag(instance, ingredients_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.SerializerMethodField()
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        image = obj.recipe.image
        if image:
            return image.url
        return None


class RecipeDetailSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
