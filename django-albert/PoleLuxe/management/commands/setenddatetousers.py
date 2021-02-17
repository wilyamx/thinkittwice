import datetime

from django.core.management import BaseCommand

from PoleLuxe.models.app import App
from PoleLuxe.models.company import Company
from PoleLuxe.models.user import (
    User,
)


class Command(BaseCommand):
    """
    Set users end_date for future inactive status
    e.g.
    ./manage.py setendatetousers {0,1,2} 'app_code1,app_code2' '2020-06-10'
    ./manage.py setendatetousers {0,1,2} 'app_code1' '2020-06-10' --include-cms-users
    """
    APP_CODES_OPTION_TYPE = 0
    PRODUCT_GROUPS_OPTION_TYPE = 1
    USER_GROUPS_OPTION_TYPE = 2

    def add_arguments(self, parser):
        parser.add_argument('input_type', help='input type', type=int)
        parser.add_argument('filter_list', help='filter list (comma separated)', type=str)
        parser.add_argument('end_date', help='end date (yyyy-mm-dd)', type=str)
        parser.add_argument(
            '--include-cms-users',
            help='include cms users',
            default=False,
            action='store_true'
        )

    def handle(self, *args, **options):
        input_type = options['input_type']
        filter_list = list(options['filter_list'].split(','))
        end_date_str = options['end_date']
        include_cms_users = options['include_cms_users']

        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

        if input_type == self.APP_CODES_OPTION_TYPE:
            app_ids = App.objects.filter(
                code__in=filter_list
            ).values_list('id', flat=True)
            if len(app_ids):
                company_list = Company.objects.filter(
                    app_id__in=app_ids
                ).values_list('id', flat=True)

                # we won't include inactive user changed by worker
                # through deactivateusersbyenddate
                user_queryset = User.objects.filter(
                    company_id__in=list(company_list),
                    active=True
                )
                if not include_cms_users:
                    user_queryset = user_queryset.exclude(
                        django_user__is_staff=True
                    )

                user_queryset.update(
                    end_date=end_date
                )
                print('Updated end-date to {} for {} user(s) to apps(s) {}'.format(
                    end_date_str,
                    user_queryset.count(),
                    filter_list
                ))

        elif input_type == self.PRODUCT_GROUPS_OPTION_TYPE:
            print('This option {} is not yet available!'.format(
                input_type
            ))
        elif input_type == self.USER_GROUPS_OPTION_TYPE:
            print('This option {} is not yet available!'.format(
                input_type
            ))
