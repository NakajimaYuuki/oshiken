from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = '初期データ投入バッチ'

    def handle(self, *args, **options):

        fixtures_json = 'initial_data'
        call_command('loaddata', fixtures_json)
