from math import trunc
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
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

class BreedListView(LoginRequiredMixin, ListView):
    model = Breed
    template_name = 'sheep/breed_list.html'
    context_object_name = 'breeds'
    ordering = ['name']

class BreedDetailView(LoginRequiredMixin, DetailView):
    model = Breed
    template_name = 'sheep/breed_detail.html'
    context_object_name = 'breed'

class BreedCreateView(LoginRequiredMixin, CreateView):
    model = Breed
    form_class = BreedForm
    template_name = 'sheep/breed_form.html'
    success_url = reverse_lazy('breed-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Breed '{form.instance.name}' created successfully!")
        return super().form_valid(form)

class BreedUpdateView(LoginRequiredMixin, UpdateView):
    model = Breed
    form_class = BreedForm
    template_name = 'sheep/breed_form.html'
    success_url = reverse_lazy('breed-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Breed '{form.instance.name}' updated successfully!")
        return super().form_valid(form)
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('breed-detail', kwargs={'pk': self.object.id})

class BreedDeleteView(LoginRequiredMixin, DeleteView):
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
        'date_acquired', 'date_removed', 'removal_reason', 'status', 'primary_image', 'notes', 'cull_candidate', 'cull_date', 'cull_reason', 
        'bottle_lamb', 'bottle_lamb_reason', 'body_type', 'udder_type', 'feet_type']
        widgets = {
            'date_acquired': forms.DateInput(attrs={'type': 'date'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_removed': forms.DateInput(attrs={'type': 'date'}),
            'cull_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'cull_reason': forms.Textarea(attrs={'rows': 3}),
            'bottle_lamb_reason': forms.Textarea(attrs={'rows': 3}),
            'removal_reason': forms.Textarea(attrs={'rows': 3})
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter mother and father fields to show only appropriate gender
        self.fields['mother'].queryset = Sheep.objects.filter(gender='F').order_by('tag_number')
        self.fields['father'].queryset = Sheep.objects.filter(gender='M').order_by('tag_number')

class SheepListView(LoginRequiredMixin, ListView):
    model = Sheep
    template_name = 'sheep/sheep_list.html'
    context_object_name = 'sheep_list'
    ordering = ['-updated_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.GET.get('status')
        if not status_filter:
            status_filter = 'ACTIVE'
        queryset = queryset.filter(status=status_filter)
        sort_param = self.request.GET.get('sort')
        if sort_param in ['tag_number', '-tag_number', 'updated_at', '-updated_at']:
            queryset = queryset.order_by(sort_param)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Sheep.STATUS_CHOICES
        if not self.request.GET.get('status'):
            context['current_status'] = 'ACTIVE'
        else:
            context['current_status'] = self.request.GET.get('status', '')
        sort_param = self.request.GET.get('sort', '')
        if sort_param.startswith('-'):
            context['current_sort'] = sort_param[1:]
            context['current_sort_dir'] = 'desc'
        elif sort_param:
            context['current_sort'] = sort_param
            context['current_sort_dir'] = 'asc'
        else:
            context['current_sort'] = 'updated_at'
            context['current_sort_dir'] = 'asc'
        return context

class SheepDetailView(LoginRequiredMixin, DetailView):
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
        if sheep.gender == 'F':
            context['breeding_records'] = BreedingRecord.objects.filter(ewe=sheep).order_by('-date_started')
            context['lambing_records'] = LambingRecord.objects.filter(ewe=sheep).order_by('-date')
        else:
            context['breeding_records'] = BreedingRecord.objects.filter(ram=sheep).order_by('-date_started')
            context['lambing_records'] = None
        
        # Get health records
        context['offspring_with_lambing'] = Sheep.objects.filter(
                models.Q(mother=sheep) | models.Q(father=sheep)).order_by('-date_of_birth')
        context['health_records'] = HealthRecord.objects.filter(sheep=sheep).order_by('-date')
        
        # Get images
        context['images'] = SheepImage.objects.filter(sheep_additional=sheep)
        
        return context

class SheepCreateView(LoginRequiredMixin, CreateView):
    model = Sheep
    form_class = SheepForm
    template_name = 'sheep/sheep_form.html'
    success_url = reverse_lazy('sheep-list')
    
    def get_initial(self):
        initial = super().get_initial()
        formtitle = self.request.GET.get('formtitle')
        if formtitle:
            initial['formtitle'] = formtitle
        mother_id = self.request.GET.get('mother')
        if mother_id:
            initial['mother'] = Sheep.objects.get(pk=mother_id)
        # If coming from a lambing record, pre-fill some fields
        lambing_id = self.request.GET.get('lambing_id')
        if lambing_id:
            try:
                lambing = LambingRecord.objects.get(pk=lambing_id)
                initial['mother'] = lambing.ewe
                initial['breed'] = lambing.ewe.breed
                if lambing.breeding_record:
                    initial['father'] = lambing.breeding_record.ram
                initial['date_of_birth'] = lambing.date
                initial['birth_record'] = lambing
            except LambingRecord.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        messages.success(self.request, f"Sheep '{form.instance.tag_number}' created successfully!")
        return super().form_valid(form)
    
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return super().get_success_url()

class SheepUpdateView(LoginRequiredMixin, UpdateView):
    model = Sheep
    form_class = SheepForm
    template_name = 'sheep/sheep_form.html'
    success_url = reverse_lazy('sheep-list')
    
    def get_success_url(self):
        return reverse_lazy('sheep-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Sheep '{form.instance.tag_number}' updated successfully!")
        return super().form_valid(form)
        
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return super().get_success_url()

class SheepDeleteView(LoginRequiredMixin, DeleteView):
    model = Sheep
    template_name = 'sheep/sheep_confirm_delete.html'
    success_url = reverse_lazy('sheep-list')
    context_object_name = 'sheep'
    
    def delete(self, request, *args, **kwargs):
        sheep = self.get_object()
        messages.success(request, f"Sheep '{sheep.tag_number}' deleted successfully!")
        return super().delete(request, *args, **kwargs)
        
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return super().get_success_url()

# New View: List sheep grouped by birth year
class SheepBirthYearListView(LoginRequiredMixin, ListView):
    model = Sheep
    template_name = 'sheep/sheep_birthyear_list.html'
    context_object_name = 'sheep_list'

    def get_queryset(self):
        # We'll handle filtering in get_context_data for more flexibility
        # Just return all sheep with birth dates
        return Sheep.objects.exclude(date_of_birth__isnull=True).order_by('-date_of_birth')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all unique years from sheep birth dates
        all_years = Sheep.objects.exclude(date_of_birth__isnull=True).dates('date_of_birth', 'year')
        context['available_years'] = sorted([date.year for date in all_years], reverse=True)
        
        # Get the selected year (if any)
        selected_year = self.request.GET.get('year')
        
        # Check if only active sheep should be shown
        # First check if the form was submitted using our hidden field
        active_only_submitted = self.request.GET.get('active_only_submitted')
        if active_only_submitted:
            # Form was submitted, checkbox state is determined by presence of active_only
            active_only = self.request.GET.get('active_only') == 'true'
        else:
            # Form was not submitted yet, default to showing active only
            active_only = True
        context['active_only'] = active_only
        
        # Filter sheep list based on the active_only parameter
        sheep_list = context['sheep_list']
        if active_only:
            sheep_list = [sheep for sheep in sheep_list if sheep.status == 'ACTIVE']
        
        if selected_year and selected_year.isdigit():
            # User has selected a specific year
            selected_year = int(selected_year)
            context['selected_year'] = selected_year
            
            # Filter sheep for the selected year
            filtered_sheep = []
            for sheep in sheep_list:
                if sheep.date_of_birth and sheep.date_of_birth.year == selected_year:
                    filtered_sheep.append(sheep)
            
            # Sort filtered sheep by gender and tag number, same as year groups
            filtered_sheep = sorted(filtered_sheep, key=lambda x: (x.gender, x.tag_number))
            
            context['filtered_sheep'] = filtered_sheep
            context['year_groups'] = None  # No need for groups when filtering by year
        else:
            # User is viewing all years - group sheep by birth year
            context['selected_year'] = None
            year_groups = []
            
            # Group sheep by birth year
            sheep_by_year = {}
            for sheep in sheep_list:
                if sheep.date_of_birth:
                    year = sheep.date_of_birth.year
                    if year not in sheep_by_year:
                        sheep_by_year[year] = []
                    sheep_by_year[year].append(sheep)
                else:
                    if 'Unknown' not in sheep_by_year:
                        sheep_by_year['Unknown'] = []
                    sheep_by_year['Unknown'].append(sheep)
            
            # Convert to list of (year, sheep_list) tuples and sort by year (descending)
            for year in sorted(sheep_by_year.keys(), reverse=True):
                sheep_count = len(sheep_by_year[year])
                year_groups.append({
                    'year': year,
                    'sheep_list': sheep_by_year[year],
                    'count': sheep_count
                })
            
            # for each year group, sort by male/female and the by tag number
            for year_group in year_groups:
                year_group['sheep_list'] = sorted(year_group['sheep_list'], key=lambda x: (x.gender, x.tag_number))
            
            context['year_groups'] = year_groups
            context['filtered_sheep'] = None
        
        return context

# Sheep Image Form
class SheepImageForm(forms.ModelForm):
    class Meta:
        model = SheepImage
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Optional description of the image'}),
        }

# Add Image to Sheep View
class SheepImageCreateView(LoginRequiredMixin, CreateView):
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
class SheepImageDeleteView(LoginRequiredMixin, DeleteView):
    model = SheepImage
    template_name = 'sheep/sheep_image_confirm_delete.html'
    context_object_name = 'image'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the first sheep from the ManyToManyField
        if self.get_object().sheep_additional.exists():
            context['sheep'] = self.get_object().sheep_additional.first()
        return context
    
    def get_success_url(self):
        # Get the first sheep from the ManyToManyField
        if self.get_object().sheep_additional.exists():
            sheep = self.get_object().sheep_additional.first()
            return reverse_lazy('sheep-detail', kwargs={'pk': sheep.pk})
        return reverse_lazy('sheep-list')
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        # Get the first sheep from the ManyToManyField
        if image.sheep_additional.exists():
            sheep = image.sheep_additional.first()
            messages.success(request, f"Image deleted from sheep '{sheep.tag_number}' successfully!")
        else:
            messages.success(request, "Image deleted successfully!")
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

class BreedingRecordListView(LoginRequiredMixin, ListView):
    model = BreedingRecord
    template_name = 'sheep/breeding_record_list.html'
    context_object_name = 'breeding_records'
    ordering = ['-date_started']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = BreedingRecord.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        return context

class BreedingRecordDetailView(LoginRequiredMixin, DetailView):
    model = BreedingRecord
    template_name = 'sheep/breeding_record_detail.html'
    context_object_name = 'breeding_record'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        breeding_record = self.get_object()
        return context

class BreedingRecordCreateView(LoginRequiredMixin, CreateView):
    model = BreedingRecord
    form_class = BreedingRecordForm
    template_name = 'sheep/breeding_record_form.html'
    success_url = reverse_lazy('breeding-record-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Breeding record created successfully!")
        return super().form_valid(form)

class EweBreedingRecordCreateView(LoginRequiredMixin, CreateView):
    model = BreedingRecord
    form_class = BreedingRecordForm
    template_name = 'sheep/breeding_record_form.html'
    success_url = reverse_lazy('breeding-record-list')
    
    def get_initial(self):
        initial = super().get_initial()
        ewe = get_object_or_404(Sheep, pk=self.kwargs['pk'])
        initial['ewe'] = ewe
        return initial
    
    def form_valid(self, form):
        messages.success(self.request, f"Breeding record created successfully!")
        return super().form_valid(form)
        
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('sheep-detail', kwargs={'pk': self.object.ewe.pk})

class BreedingRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = BreedingRecord
    form_class = BreedingRecordForm
    template_name = 'sheep/breeding_record_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        initial['ewe'] = self.object.ewe
        return initial
    
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('breeding-record-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Breeding record updated successfully!")
        return super().form_valid(form)

class BreedingRecordDeleteView(LoginRequiredMixin, DeleteView):
    model = BreedingRecord
    template_name = 'sheep/breeding_record_confirm_delete.html'
    success_url = reverse_lazy('breeding-record-list')
    context_object_name = 'breeding_record'
    
    def delete(self, request, *args, **kwargs):
        breeding_record = self.get_object()
        messages.success(request, f"Breeding record deleted successfully!")
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('breeding-record-detail', kwargs={'pk': self.object.pk})

# Duplicate Breeding Record function
@login_required
def duplicate_breeding_record(request, pk):
    # Get the original breeding record
    original_record = get_object_or_404(BreedingRecord, pk=pk)
    
    # Create a new record with the same data
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
    messages.success(request, f"Breeding record duplicated successfully!")
    
    # Redirect to edit page for the new record
    return redirect('breeding-record-update', pk=new_record.pk)

# LambingRecord Views
class LambingRecordForm(forms.ModelForm):
    class Meta:
        model = LambingRecord
        fields = ['ewe', 'date', 'assisted', 'complications', 
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
        
class LambingRecordListView(LoginRequiredMixin, ListView):
    model = LambingRecord
    template_name = 'sheep/lambing_record_list.html'
    context_object_name = 'lambing_records'
    ordering = ['-date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LambingRecordDetailView(LoginRequiredMixin, DetailView):
    model = LambingRecord
    template_name = 'sheep/lambing_record_detail.html'
    context_object_name = 'lambing_record'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get lambs associated with this lambing record using the new relationship
        context['lambs'] = self.object.lambs.all()
        return context

class LambingRecordCreateView(LoginRequiredMixin, CreateView):
    model = LambingRecord
    form_class = LambingRecordForm
    template_name = 'sheep/lambing_record_form.html'
    success_url = reverse_lazy('lambing-record-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Lambing record created successfully!")
        return super().form_valid(form)

class EweLambingRecordCreateView(LoginRequiredMixin, CreateView):
    model = LambingRecord
    form_class = LambingRecordForm
    template_name = 'sheep/lambing_record_form.html'
    success_url = reverse_lazy('lambing-record-list')
    
    def get_initial(self):
        initial = super().get_initial()
        ewe = get_object_or_404(Sheep, pk=self.kwargs['pk'])
        initial['ewe'] = ewe
        return initial

    def form_valid(self, form):
        messages.success(self.request, f"Lambing record created successfully!")
        return super().form_valid(form)
        
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('sheep-detail', kwargs={'pk': self.kwargs['pk']})

class LambingRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = LambingRecord
    form_class = LambingRecordForm
    template_name = 'sheep/lambing_record_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        initial['ewe'] = self.object.ewe
        return initial
    
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('lambing-record-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Lambing record updated successfully!")
        return super().form_valid(form)

class LambingRecordDeleteView(LoginRequiredMixin, DeleteView):
    model = LambingRecord
    template_name = 'sheep/lambing_record_confirm_delete.html'
    success_url = reverse_lazy('lambing-record-list')
    context_object_name = 'lambing_record'
    
    def delete(self, request, *args, **kwargs):
        lambing_record = self.get_object()
        messages.success(request, f"Lambing record deleted successfully!")
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('sheep-detail', kwargs={'pk': self.object.ewe.pk})

# LambingImage Form
class LambingImageForm(forms.ModelForm):
    class Meta:
        model = LambingImage
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Optional description of the image'}),
        }

# Add Image to Lambing Record View
class LambingImageCreateView(LoginRequiredMixin, CreateView):
    model = LambingImage
    form_class = LambingImageForm
    template_name = 'sheep/lambing_image_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lambing_id = self.kwargs.get('pk')
        context['lambing_record'] = get_object_or_404(LambingRecord, pk=lambing_id)
        return context
    
    def form_valid(self, form):
        # Create the image but don't save to DB yet
        image = form.save(commit=False)
        image.save()  # Save to get an ID
        
        lambing_id = self.kwargs.get('pk')
        lamb = get_object_or_404(LambingRecord, pk=lambing_id)
        lamb.additional_images.add(image)

        messages.success(self.request, f"Image added to lamb successfully!")
        return super().form_valid(form)
    
    def get_success_url(self):
        lambing_id = self.kwargs.get('pk')
        return reverse_lazy('lambing-record-detail', kwargs={'pk': lambing_id})

# Delete Lambing Image View
class LambingImageDeleteView(LoginRequiredMixin, DeleteView):
    model = LambingImage
    template_name = 'sheep/lambing_image_confirm_delete.html'
    context_object_name = 'image'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        image = self.get_object()
        # Get the lambing record associated with this image
        if hasattr(image, 'lambing_records') and image.lambing_records.exists():
            context['lambing_record'] = image.lambing_records.first()
        return context
    
    def get_success_url(self):
        lambing_record = self.get_object().lambing_records.first()
        return reverse_lazy('lambing-record-detail', kwargs={'pk': lambing_record.pk})
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        messages.success(request, f"Image deleted from lambing record successfully!")
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

class HealthRecordListView(LoginRequiredMixin, ListView):
    model = HealthRecord
    template_name = 'sheep/health_record_list.html'
    context_object_name = 'health_records'
    ordering = ['-date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record_types'] = dict(HealthRecord.TYPE_CHOICES)
        return context

class HealthRecordDetailView(LoginRequiredMixin, DetailView):
    model = HealthRecord
    template_name = 'sheep/health_record_detail.html'
    context_object_name = 'health_record'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class HealthRecordCreateView(LoginRequiredMixin, CreateView):
    model = HealthRecord
    form_class = HealthRecordForm
    template_name = 'sheep/health_record_form.html'
    success_url = reverse_lazy('health-record-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Health record created successfully!")
        return super().form_valid(form)

class HealthRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = HealthRecord
    form_class = HealthRecordForm
    template_name = 'sheep/health_record_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        initial['sheep'] = self.object.sheep
        return initial
    
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('health-record-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Health record updated successfully!")
        return super().form_valid(form)

class HealthRecordDeleteView(LoginRequiredMixin, DeleteView):
    model = HealthRecord
    template_name = 'sheep/health_record_confirm_delete.html'
    success_url = reverse_lazy('health-record-list')
    context_object_name = 'health_record'
    
    def delete(self, request, *args, **kwargs):
        health_record = self.get_object()
        messages.success(request, f"Health record deleted successfully!")
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('health-record-detail', kwargs={'pk': self.object.pk})

class EweHealthRecordCreateView(LoginRequiredMixin, CreateView):
    model = HealthRecord
    form_class = HealthRecordForm
    template_name = 'sheep/health_record_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        ewe = get_object_or_404(Sheep, pk=self.kwargs['pk'])
        initial['sheep'] = ewe
        return initial

    def get_success_url(self):
        # If next parameter is provided, redirect there
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('sheep-detail', kwargs={'pk': self.kwargs['pk']})
