from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db import models

from .models import Breed, Sheep, SheepImage, BreedingRecord, LambingRecord, LambingImage, HealthRecord
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
        fields = ['tag_number', 'name', 'gender', 'breed', 'mother', 'father', 'birth_record', 'weight_current', 'date_of_birth',
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
        sheep = self.get_object()
        
        # Get offspring
        context['offspring'] = Sheep.objects.filter(
            models.Q(mother=sheep) | models.Q(father=sheep)
        ).order_by('-date_of_birth')
        
        # Get breeding records
        context['breeding_records'] = BreedingRecord.objects.filter(
            models.Q(ewe=sheep) | models.Q(ram=sheep)
        ).order_by('-date_started')
        
        # Get lambing records
        if sheep.gender == 'F':
            context['lambing_records'] = LambingRecord.objects.filter(
                ewe=sheep
            ).order_by('-date')
        
        # Get health records
        context['health_records'] = HealthRecord.objects.filter(
            sheep=sheep
        ).order_by('-date')
        
        return context

class SheepCreateView(CreateView):
    model = Sheep
    form_class = SheepForm
    template_name = 'sheep/sheep_form.html'
    success_url = reverse_lazy('sheep-list')
    
    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill form fields if provided in GET parameters
        if 'mother' in self.request.GET:
            initial['mother'] = self.request.GET.get('mother')
        if 'father' in self.request.GET:
            initial['father'] = self.request.GET.get('father')
        if 'birth_record' in self.request.GET:
            initial['birth_record'] = self.request.GET.get('birth_record')
        if 'date_of_birth' in self.request.GET:
            initial['date_of_birth'] = self.request.GET.get('date_of_birth')
        return initial
    
    def form_valid(self, form):
        # If creating a lamb from a lambing record, ensure birth_record is set
        if 'birth_record' in self.request.GET:
            birth_record_id = self.request.GET.get('birth_record')
            form.instance.birth_record_id = birth_record_id
        
        messages.success(self.request, f"Sheep '{form.instance.tag_number}' created successfully!")
        return super().form_valid(form)
    
    def get_success_url(self):
        # If creating a lamb from a lambing record, redirect back to the lambing record
        if 'birth_record' in self.request.GET:
            return reverse_lazy('lambing-record-detail', kwargs={'pk': self.request.GET.get('birth_record')})
        return self.success_url

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

# BreedingRecord Views
class BreedingRecordForm(forms.ModelForm):
    class Meta:
        model = BreedingRecord
        fields = ['ewe', 'ram', 'date_started', 'date_ended', 'expected_lambing_date', 'status', 'notes']
        widgets = {
            'date_started': forms.DateInput(attrs={'type': 'date'}),
            'date_ended': forms.DateInput(attrs={'type': 'date'}),
            'expected_lambing_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

class BreedingRecordListView(ListView):
    model = BreedingRecord
    template_name = 'sheep/breeding_record_list.html'
    context_object_name = 'breeding_records'
    ordering = ['-date_started']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by status if provided in GET parameters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = BreedingRecord.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        return context

class BreedingRecordDetailView(DetailView):
    model = BreedingRecord
    template_name = 'sheep/breeding_record_detail.html'
    context_object_name = 'breeding_record'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related lambing record if it exists
        breeding_record = self.get_object()
        try:
            context['lambing_record'] = breeding_record.lambing
        except:
            context['lambing_record'] = None
        return context

class BreedingRecordCreateView(CreateView):
    model = BreedingRecord
    form_class = BreedingRecordForm
    template_name = 'sheep/breeding_record_form.html'
    success_url = reverse_lazy('breeding-record-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Breeding record created successfully!")
        return super().form_valid(form)

class BreedingRecordUpdateView(UpdateView):
    model = BreedingRecord
    form_class = BreedingRecordForm
    template_name = 'sheep/breeding_record_form.html'
    
    def get_success_url(self):
        return reverse_lazy('breeding-record-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Breeding record updated successfully!")
        return super().form_valid(form)

class BreedingRecordDeleteView(DeleteView):
    model = BreedingRecord
    template_name = 'sheep/breeding_record_confirm_delete.html'
    success_url = reverse_lazy('breeding-record-list')
    context_object_name = 'breeding_record'
    
    def delete(self, request, *args, **kwargs):
        breeding_record = self.get_object()
        messages.success(request, f"Breeding record for {breeding_record.ewe} and {breeding_record.ram} deleted successfully!")
        return super().delete(request, *args, **kwargs)

# Duplicate Breeding Record function
def duplicate_breeding_record(request, pk):
    # Get the original breeding record
    original_record = get_object_or_404(BreedingRecord, pk=pk)
    
    # Create a new record with the same data but reset some fields
    new_record = BreedingRecord(
        ewe=original_record.ewe,
        ram=original_record.ram,
        date_started=original_record.date_started,
        date_ended=original_record.date_ended,
        expected_lambing_date=original_record.expected_lambing_date,
        status=original_record.status,
        notes=original_record.notes
    )
    
    # Save the new record
    new_record.save()
    
    # Add success message
    messages.success(request, f"Breeding record duplicated successfully! You can now edit the new record.")
    
    # Redirect to edit page for the new record
    return redirect('breeding-record-update', pk=new_record.pk)

# LambingRecord Views
class LambingRecordForm(forms.ModelForm):
    class Meta:
        model = LambingRecord
        fields = ['breeding_record', 'ewe', 'date', 'assisted', 'complications', 
                 'total_born', 'born_alive', 'born_dead', 'primary_image', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'complications': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter ewe field to show only females
        self.fields['ewe'].queryset = Sheep.objects.filter(gender='F')
        # Filter breeding records to show only those without lambing records
        if not self.instance.pk:  # Only for new records
            existing_lambing_breeding_records = LambingRecord.objects.exclude(
                pk=self.instance.pk if self.instance.pk else None
            ).values_list('breeding_record', flat=True)
            self.fields['breeding_record'].queryset = BreedingRecord.objects.exclude(
                pk__in=existing_lambing_breeding_records
            )

class LambingRecordListView(ListView):
    model = LambingRecord
    template_name = 'sheep/lambing_record_list.html'
    context_object_name = 'lambing_records'
    ordering = ['-date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LambingRecordDetailView(DetailView):
    model = LambingRecord
    template_name = 'sheep/lambing_record_detail.html'
    context_object_name = 'lambing_record'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get lambs associated with this lambing record using the new relationship
        context['lambs'] = self.object.lambs.all()
        return context

class LambingRecordCreateView(CreateView):
    model = LambingRecord
    form_class = LambingRecordForm
    template_name = 'sheep/lambing_record_form.html'
    success_url = reverse_lazy('lambing-record-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Lambing record for {form.instance.ewe} on {form.instance.date} created successfully!")
        return super().form_valid(form)

class LambingRecordUpdateView(UpdateView):
    model = LambingRecord
    form_class = LambingRecordForm
    template_name = 'sheep/lambing_record_form.html'
    
    def get_success_url(self):
        return reverse_lazy('lambing-record-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Lambing record for {form.instance.ewe} on {form.instance.date} updated successfully!")
        return super().form_valid(form)

class LambingRecordDeleteView(DeleteView):
    model = LambingRecord
    template_name = 'sheep/lambing_record_confirm_delete.html'
    success_url = reverse_lazy('lambing-record-list')
    context_object_name = 'lambing_record'
    
    def delete(self, request, *args, **kwargs):
        lambing_record = self.get_object()
        messages.success(request, f"Lambing record for {lambing_record.ewe} on {lambing_record.date} deleted successfully!")
        return super().delete(request, *args, **kwargs)

# LambingImage Form
class LambingImageForm(forms.ModelForm):
    class Meta:
        model = LambingImage
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Optional description of the image'}),
        }

# Add Image to Lambing Record View
class LambingImageCreateView(CreateView):
    model = LambingImage
    form_class = LambingImageForm
    template_name = 'sheep/lambing_image_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lambing_record'] = get_object_or_404(LambingRecord, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        lambing_record = get_object_or_404(LambingRecord, pk=self.kwargs['pk'])
        image = form.save()
        lambing_record.additional_images.add(image)
        messages.success(self.request, "Image added to lambing record successfully!")
        return redirect('lambing-record-detail', pk=lambing_record.pk)

# Delete Lambing Image View
class LambingImageDeleteView(DeleteView):
    model = LambingImage
    template_name = 'sheep/lambing_image_confirm_delete.html'
    context_object_name = 'image'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Find the lambing record this image belongs to
        for lambing_record in self.object.lambing_records.all():
            context['lambing_record'] = lambing_record
            break
        return context
    
    def get_success_url(self):
        # Redirect back to the lambing record detail page
        for lambing_record in self.object.lambing_records.all():
            return reverse_lazy('lambing-record-detail', kwargs={'pk': lambing_record.pk})
        return reverse_lazy('lambing-record-list')
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        messages.success(request, "Image deleted from lambing record successfully!")
        return super().delete(request, *args, **kwargs)

# HealthRecord Views
class HealthRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ['sheep', 'date', 'record_type', 'treatment', 'dosage', 'administered_by', 
                 'requires_followup', 'followup_date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'followup_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

class HealthRecordListView(ListView):
    model = HealthRecord
    template_name = 'sheep/health_record_list.html'
    context_object_name = 'health_records'
    ordering = ['-date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record_types'] = dict(HealthRecord.TYPE_CHOICES)
        return context

class HealthRecordDetailView(DetailView):
    model = HealthRecord
    template_name = 'sheep/health_record_detail.html'
    context_object_name = 'health_record'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class HealthRecordCreateView(CreateView):
    model = HealthRecord
    form_class = HealthRecordForm
    template_name = 'sheep/health_record_form.html'
    success_url = reverse_lazy('health-record-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Health record for {form.instance.sheep} created successfully!")
        return super().form_valid(form)

class HealthRecordUpdateView(UpdateView):
    model = HealthRecord
    form_class = HealthRecordForm
    template_name = 'sheep/health_record_form.html'
    
    def get_success_url(self):
        return reverse_lazy('health-record-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Health record for {form.instance.sheep} updated successfully!")
        return super().form_valid(form)

class HealthRecordDeleteView(DeleteView):
    model = HealthRecord
    template_name = 'sheep/health_record_confirm_delete.html'
    success_url = reverse_lazy('health-record-list')
    context_object_name = 'health_record'
    
    def delete(self, request, *args, **kwargs):
        health_record = self.get_object()
        messages.success(request, f"Health record for {health_record.sheep} deleted successfully!")
        return super().delete(request, *args, **kwargs)
