from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.db.models import Exists, OuterRef

from .constants import (
    COOKING_TIME, INGREDIENT_AMOUNT,
    INGRS_NAME_LENGTH, MEASUREMENTS,
    RECIPE_NAME_LENGTH, TAG_NAME_LENGTH, TAG_SLUG)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_NAME_LENGTH,
        unique=True,
        verbose_name='Название')
    slug = models.SlugField(
        max_length=TAG_SLUG,
        unique=True,
        verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGRS_NAME_LENGTH,
        verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=MEASUREMENTS,
        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ['name']
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class RecipeQuerySet(models.QuerySet):
    def get_is_favorited_is_in_shopping_cart(self, request_user):
        if request_user.is_authenticated:
            self = self.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=request_user,
                        recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=request_user,
                        recipe=OuterRef('pk')
                    )
                ),
            )
        else:
            self = self.annotate(
                is_favorited=Exists(Favorite.objects.none()),
                is_in_shopping_cart=Exists(ShoppingCart.objects.none()),
            )
        return self


class Recipe(models.Model):
    name = models.CharField(
        max_length=RECIPE_NAME_LENGTH,
        verbose_name='Название'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='authored_recipes',
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингридиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги')
    image = models.ImageField(
        upload_to='recipes/image',
        verbose_name='Картинка'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[validators.MinValueValidator(
            COOKING_TIME,
            message=f'Минимальное значение {COOKING_TIME}!')],
        verbose_name='Время приготовления'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        null=True
    )
    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author.email}, {self.name}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes'
    )
    amount = models.PositiveSmallIntegerField(
        default=COOKING_TIME,
        validators=[
            validators.MinValueValidator(
                INGREDIENT_AMOUNT,
                message=f'Минимальное значение {INGREDIENT_AMOUNT}!')],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ['amount']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_recipe')]

    def __str__(self) -> str:
        return f'{self.recipe} {self.ingredient}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        null=True
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина',
        verbose_name_plural = 'Корзина'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='user_recipe_shopping_cart_unique'),
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Корзину покупок'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        null=True
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='user_recipe_favorite_unique'),
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'
