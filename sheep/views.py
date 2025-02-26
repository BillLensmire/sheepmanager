from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone

from .models import Breed, Sheep, SheepImage, BreedingRecord, LambingRecord, LambingImage
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
        context['breeding_records'] = BreedingRecord.objects.filter(ewe=sheep) | BreedingRecord.objects.filter(ram=sheep)
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
        # Get lambs associated with this lambing record (if any)
        # This assumes lambs have a ForeignKey to LambingRecord
        # If not, this would need to be adjusted based on your data model
        context['lambs'] = Sheep.objects.filter(
            mother=self.object.ewe,
            date_of_birth=self.object.date
        )
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
