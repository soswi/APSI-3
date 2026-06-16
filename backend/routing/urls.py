from django.urls import path

from .views import (
    recent_routes_view, 
    saved_route_detail_view, 
    saved_routes_view, 
    walking_route_view,
    share_route_view,
    pending_shares_view,
    accept_share_view,
    reject_share_view
)

urlpatterns = [
    path('walking', walking_route_view, name='walking-route'),
    path('recent', recent_routes_view, name='recent-routes'),
    path('saved', saved_routes_view, name='saved-routes'),
    path('saved/<int:route_id>', saved_route_detail_view, name='saved-route-detail'),
    path('<int:route_id>/share', share_route_view, name='share-route'),
    path('shares/pending', pending_shares_view, name='pending-shares'),
    path('shares/<int:share_id>/accept', accept_share_view, name='accept-share'),
    path('shares/<int:share_id>/reject', reject_share_view, name='reject-share'),
]
