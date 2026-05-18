from django.urls import path

from .views import walking_route_view

urlpatterns = [
    path('walking', walking_route_view, name='walking-route'),
]
