from django.urls import path
from . import views

urlpatterns = [
    # Breed URLs
    path('breeds/', views.BreedListView.as_view(), name='breed-list'),
    path('breeds/new/', views.BreedCreateView.as_view(), name='breed-create'),
    path('breeds/<int:pk>/', views.BreedDetailView.as_view(), name='breed-detail'),
    path('breeds/<int:pk>/edit/', views.BreedUpdateView.as_view(), name='breed-update'),
    path('breeds/<int:pk>/delete/', views.BreedDeleteView.as_view(), name='breed-delete'),
    
    # Sheep URLs
    path('sheep/', views.SheepListView.as_view(), name='sheep-list'),
    path('sheep/new/', views.SheepCreateView.as_view(), name='sheep-create'),
    path('sheep/<int:pk>/', views.SheepDetailView.as_view(), name='sheep-detail'),
    path('sheep/<int:pk>/edit/', views.SheepUpdateView.as_view(), name='sheep-update'),
    path('sheep/<int:pk>/delete/', views.SheepDeleteView.as_view(), name='sheep-delete'),
]
