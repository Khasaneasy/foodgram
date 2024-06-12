from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название')
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['id']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_recipes',
        verbose_name='Автор'
    )
    is_favorited = models.ManyToManyField(
        User,
        through='Favorite',
        related_name='favorited_recipes',
        verbose_name='В избранном'
    )
    is_in_shopping_cart = models.ManyToManyField(
        User,
        through='ShoppingCart',
        related_name='shopping_cart_recipes',
        verbose_name='В корзине',
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
        blank=False,
        validators=[validators.MinValueValidator(
            1,
            message='Минимальное время приготовления 1 минута')],
        verbose_name='Время приготовления'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        null=True
    )

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
        default=1,
        validators=(
            validators.MinValueValidator(
                1, message='Минмальное количество ингридиентов 1'),),
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ['-id']
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
        constraints = (
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='user_recipe_shopping_cart_unique'),
        )

    def str(self):
        list_ = [item.name for item in self.recipe.all()]
        return f'Пользователь {self.user} добавил {[item for item in list_]}'\
            'в корзину.'


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
        constraints = (
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='user_recipe_favorite_unique'),
        )

    def str(self):
        list_ = [item.name for item in self.recipe.all()]
        return f'Пользователь {self.user} добавил {[item for item in list_]}'\
            'в избранные.'
