from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Breed, Sheep, SheepImage
from django import forms

# Create your views here.

class BreedForm(forms.ModelForm):
    class Meta:
        model = Breed
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class BreedListView(ListView):
    model = Breed
    template_name = 'sheep/breed_list.html'
    context_object_name = 'breeds'
    ordering = ['name']

class BreedDetailView(DetailView):
    model = Breed
    template_name = 'sheep/breed_detail.html'
    context_object_name = 'breed'

class BreedCreateView(CreateView):
    model = Breed
    form_class = BreedForm
    template_name = 'sheep/breed_form.html'
    success_url = reverse_lazy('breed-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Breed '{form.instance.name}' created successfully!")
        return super().form_valid(form)

class BreedUpdateView(UpdateView):
    model = Breed
    form_class = BreedForm
    template_name = 'sheep/breed_form.html'
    success_url = reverse_lazy('breed-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Breed '{form.instance.name}' updated successfully!")
        return super().form_valid(form)

class BreedDeleteView(DeleteView):
    model = Breed
    template_name = 'sheep/breed_confirm_delete.html'
    success_url = reverse_lazy('breed-list')
    context_object_name = 'breed'
    
    def delete(self, request, *args, **kwargs):
        breed = self.get_object()
        messages.success(request, f"Breed '{breed.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)

# Sheep Views
class SheepForm(forms.ModelForm):
    class Meta:
        model = Sheep
        fields = ['tag_number', 'name', 'gender', 'breed', 'mother', 'father', 'weight_current', 'date_of_birth',
        'date_acquired',
                 'status', 'primary_image', 'notes']
        widgets = {
            'date_acquired': forms.DateInput(attrs={'type': 'date'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter mother and father fields to show only appropriate gender
        self.fields['mother'].queryset = Sheep.objects.filter(gender='F')
        self.fields['father'].queryset = Sheep.objects.filter(gender='M')

class SheepListView(ListView):
    model = Sheep
    template_name = 'sheep/sheep_list.html'
    context_object_name = 'sheep_list'
    ordering = ['tag_number']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by status if provided in GET parameters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Sheep.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        return context

class SheepDetailView(DetailView):
    model = Sheep
    template_name = 'sheep/sheep_detail.html'
    context_object_name = 'sheep'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related records
        sheep = self.get_object()
        context['health_records'] = sheep.health_records.all().order_by('-date')[:5]
        context['lambings'] = sheep.lambings.all().order_by('-date')[:5] if sheep.gender == 'F' else None
        context['breeding_as_ram'] = sheep.breeding_as_ram.all().order_by('-date_started')[:5] if sheep.gender == 'M' else None
        context['breeding_as_ewe'] = sheep.breeding_as_ewe.all().order_by('-date_started')[:5] if sheep.gender == 'F' else None
        context['offspring'] = Sheep.objects.filter(mother=sheep) | Sheep.objects.filter(father=sheep)
        return context

class SheepCreateView(CreateView):
    model = Sheep
    form_class = SheepForm
    template_name = 'sheep/sheep_form.html'
    success_url = reverse_lazy('sheep-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Sheep '{form.instance.tag_number}' created successfully!")
        return super().form_valid(form)

class SheepUpdateView(UpdateView):
    model = Sheep
    form_class = SheepForm
    template_name = 'sheep/sheep_form.html'
    
    def get_success_url(self):
        return reverse_lazy('sheep-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Sheep '{form.instance.tag_number}' updated successfully!")
        return super().form_valid(form)

class SheepDeleteView(DeleteView):
    model = Sheep
    template_name = 'sheep/sheep_confirm_delete.html'
    success_url = reverse_lazy('sheep-list')
    context_object_name = 'sheep'
    
    def delete(self, request, *args, **kwargs):
        sheep = self.get_object()
        messages.success(request, f"Sheep '{sheep.tag_number}' deleted successfully!")
        return super().delete(request, *args, **kwargs)
