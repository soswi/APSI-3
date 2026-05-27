from django.urls import path

from .views import recent_routes_view, saved_route_detail_view, saved_routes_view, walking_route_view

urlpatterns = [
    path('walking', walking_route_view, name='walking-route'),
    path('recent', recent_routes_view, name='recent-routes'),
    path('saved', saved_routes_view, name='saved-routes'),
    path('saved/<int:route_id>', saved_route_detail_view, name='saved-route-detail'),
]
