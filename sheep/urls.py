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
    path('sheep/<int:pk>/add-image/', views.SheepImageCreateView.as_view(), name='sheep-add-image'),
    
    # Sheep Image URLs
    path('sheep/images/<int:pk>/delete/', views.SheepImageDeleteView.as_view(), name='sheep-delete-image'),
    
    # Breeding Record URLs
    path('breeding/', views.BreedingRecordListView.as_view(), name='breeding-record-list'),
    path('breeding/new/', views.BreedingRecordCreateView.as_view(), name='breeding-record-create'),
    path('breeding/<int:pk>/', views.BreedingRecordDetailView.as_view(), name='breeding-record-detail'),
    path('breeding/<int:pk>/edit/', views.BreedingRecordUpdateView.as_view(), name='breeding-record-update'),
    path('breeding/<int:pk>/delete/', views.BreedingRecordDeleteView.as_view(), name='breeding-record-delete'),
    path('breeding/<int:pk>/duplicate/', views.duplicate_breeding_record, name='breeding-record-duplicate'),
    
    # Lambing Record URLs
    path('lambing/', views.LambingRecordListView.as_view(), name='lambing-record-list'),
    path('lambing/new/', views.LambingRecordCreateView.as_view(), name='lambing-record-create'),
    path('lambing/<int:pk>/', views.LambingRecordDetailView.as_view(), name='lambing-record-detail'),
    path('lambing/<int:pk>/edit/', views.LambingRecordUpdateView.as_view(), name='lambing-record-update'),
    path('lambing/<int:pk>/delete/', views.LambingRecordDeleteView.as_view(), name='lambing-record-delete'),
    path('lambing/<int:pk>/add-image/', views.LambingImageCreateView.as_view(), name='lambing-add-image'),
    
    # Lambing Image URLs
    path('lambing/images/<int:pk>/delete/', views.LambingImageDeleteView.as_view(), name='lambing-delete-image'),
    
    # Health Record URLs
    path('health/', views.HealthRecordListView.as_view(), name='health-record-list'),
    path('health/new/', views.HealthRecordCreateView.as_view(), name='health-record-create'),
    path('health/<int:pk>/', views.HealthRecordDetailView.as_view(), name='health-record-detail'),
    path('health/<int:pk>/edit/', views.HealthRecordUpdateView.as_view(), name='health-record-update'),
    path('health/<int:pk>/delete/', views.HealthRecordDeleteView.as_view(), name='health-record-delete'),
]
