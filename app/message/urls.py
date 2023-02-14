"""
URL mappings for the message API.
"""
from django.urls import path

from message import views


app_name = 'message'

urlpatterns = [
    path('consume-data/', views.ConsumeDataView.as_view(), name='consume_data'),  # noqa: E501
    path('store-data/', views.StoreDataView.as_view(), name='store_data'),
    path('show-data/', views.ShowDataView.as_view(), name='show_data'),
]
