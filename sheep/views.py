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

# Sheep Image Form
class SheepImageForm(forms.ModelForm):
    class Meta:
        model = SheepImage
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Optional description of the image'}),
        }

# Add Image to Sheep View
class SheepImageCreateView(CreateView):
    model = SheepImage
    form_class = SheepImageForm
    template_name = 'sheep/sheep_image_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sheep_id = self.kwargs.get('pk')
        context['sheep'] = get_object_or_404(Sheep, pk=sheep_id)
        return context
    
    def form_valid(self, form):
        # Create the image but don't save to DB yet
        image = form.save(commit=False)
        image.save()  # Save to get an ID
        
        # Get the sheep and add this image to its additional_images
        sheep_id = self.kwargs.get('pk')
        sheep = get_object_or_404(Sheep, pk=sheep_id)
        sheep.additional_images.add(image)
        
        messages.success(self.request, f"Image added to {sheep.tag_number} successfully!")
        return redirect('sheep-detail', pk=sheep_id)

# Delete Sheep Image View
class SheepImageDeleteView(DeleteView):
    model = SheepImage
    template_name = 'sheep/sheep_image_confirm_delete.html'
    context_object_name = 'image'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Find which sheep this image belongs to
        image = self.get_object()
        sheep = image.sheep_additional.first()
        context['sheep'] = sheep
        return context
    
    def get_success_url(self):
        # Get the sheep this image belongs to
        image = self.get_object()
        sheep = image.sheep_additional.first()
        return reverse_lazy('sheep-detail', kwargs={'pk': sheep.id})
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        sheep = image.sheep_additional.first()
        messages.success(request, f"Image deleted from {sheep.tag_number} successfully!")
        return super().delete(request, *args, **kwargs)
