from rest_framework import pagination
from rest_framework.response import Response


class LinkHeaderPagination(pagination.PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):  # pragma: no cover
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()

        headers = {}

        if next_url is not None and previous_url is not None:
            headers = {
                'Next-Page-Link': next_url,
                'Prev-Page-Link': previous_url
            }
        elif next_url is not None:
            headers = {
                'Next-Page-Link': next_url
            }
        elif previous_url is not None:
            headers = {
                'Prev-Page-Link': previous_url
            }

        return Response(data, headers=headers)
