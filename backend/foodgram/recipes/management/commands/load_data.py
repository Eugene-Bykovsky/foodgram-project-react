import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        file_path = options['path']
        with open(file_path, encoding='utf-8') as file:
            csv_list = csv.reader(file)
            for row in csv_list:
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit)
