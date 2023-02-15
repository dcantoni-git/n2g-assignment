"""
URL mappings for the message API.
"""
from django.urls import path

from message import views


app_name = 'message'

urlpatterns = [
    path('send-to-exchange/', views.SendToExchangeView.as_view(), name='send_to_exchange'),  # noqa: E501
    path('store-to-database/', views.StoreToDatabaseView.as_view(), name='store_to_database'),  # noqa: E501
    path('show-stored-messages/', views.ShowStoredMessagesView.as_view(), name='show_stored_messages'),  # noqa: E501
]
