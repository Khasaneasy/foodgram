from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Добавление тегов'

    def handle(self, *args, **kwargs):
        data = [
            {'name': 'Ужин', 'slug': 'dinner'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Завтрак', 'slug': 'breakfast'}
        ]
        Tag.objects.bulk_create(Tag(**tag) for tag in data)
        self.stdout.write(self.style.SUCCESS('Все тэги загружены!'))
