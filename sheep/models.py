from django.db import models
from django.utils import timezone
import uuid
import os


def sheep_image_path(instance, filename):
    """Generate file path for sheep images"""
    # Get the file extension
    ext = filename.split('.')[-1]

    # Create a new filename with sheep's tag number
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Return the complete path
    return os.path.join('sheep_images', new_filename)


def lambing_image_path(instance, filename):
    """Generate file path for lambing record images"""
    # Get the file extension
    ext = filename.split('.')[-1]
    
    # Create a new filename
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Return the complete path
    return os.path.join('lambing_images', new_filename)


class Breed(models.Model):
    """Model representing sheep breeds"""
    name = models.CharField(max_length=100, default='Dorper', unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Sheep(models.Model):
    """Model representing an individual sheep"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SOLD', 'Sold'),
        ('DECEASED', 'Deceased'),
        ('CULLED', 'Culled'),
        ('HARVESTED', 'Harvested')
    ]
    
    # Identification
    tag_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(blank=True, null=True)
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, related_name='sheep')
    
    # Optional physical characteristics
    weight_birth = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight at birth in lb")
    weight_current = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Current weight in lb")
    color = models.CharField(max_length=100, blank=True)
    markings = models.TextField(blank=True)
    
    # Images
    primary_image = models.ImageField(upload_to=sheep_image_path, null=True, blank=True, help_text="Main profile image of the sheep")
    additional_images = models.ManyToManyField('SheepImage', blank=True, related_name='sheep_additional')
    
    # Lineage
    mother = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='offspring_as_mother')
    father = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='offspring_as_father')
    birth_record = models.ForeignKey('LambingRecord', null=True, blank=True, on_delete=models.SET_NULL, related_name='lambs')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    date_acquired = models.DateField(default=timezone.now)
    date_removed = models.DateField(null=True, blank=True)
    removal_reason = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "sheep"
        indexes = [
            models.Index(fields=['tag_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        if self.name:
            return f"{self.tag_number} - {self.name}"
        return self.tag_number
    
    @property
    def age(self):
        """Calculate the age of the sheep in days"""
        if self.date_of_birth:
            today = timezone.now().date()
            return (today - self.date_of_birth).days
        return None
    
    @property
    def age_years(self):
        """Calculate the age of the sheep in years (approximate)"""
        days = self.age
        if days:
            return round(days / 365, 1)
        return None


class SheepImage(models.Model):
    """Model for storing additional sheep images"""
    image = models.ImageField(upload_to=sheep_image_path)
    caption = models.CharField(max_length=255, blank=True)
    date_added = models.DateField(default=timezone.now)
    
    def __str__(self):
        if hasattr(self, 'sheep_additional') and self.sheep_additional.exists():
            sheep = self.sheep_additional.first()
            return f"Image of {sheep} - {self.caption}"
        return f"Sheep image - {self.caption}"
    
    def save(self, *args, **kwargs):        
        super().save(*args, **kwargs)


class BreedingRecord(models.Model):
    """Model representing breeding events between sheep"""
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUCCESSFUL', 'Successful'),
        ('UNSUCCESSFUL', 'Unsuccessful'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    ewe = models.ForeignKey(Sheep, on_delete=models.CASCADE, related_name='breeding_as_ewe', 
                            limit_choices_to={'gender': 'F'})
    ram = models.ForeignKey(Sheep, on_delete=models.CASCADE, related_name='breeding_as_ram',
                           limit_choices_to={'gender': 'M'})
    
    # Dates
    date_started = models.DateField()
    date_ended = models.DateField(null=True, blank=True)
    expected_lambing_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_started']
        indexes = [
            models.Index(fields=['date_started']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Breeding: {self.ewe} × {self.ram} ({self.date_started})"


class LambingRecord(models.Model):
    """Model representing a lambing event (birth of lambs)"""
    breeding_record = models.OneToOneField(BreedingRecord, on_delete=models.CASCADE, related_name='lambing',
                                         null=True, blank=True)
    ewe = models.ForeignKey(Sheep, on_delete=models.CASCADE, related_name='lambings',
                          limit_choices_to={'gender': 'F'})
    date = models.DateField()
    
    # Lambing details
    assisted = models.BooleanField(default=False)
    complications = models.TextField(blank=True)
    
    # Counts
    total_born = models.PositiveSmallIntegerField(default=1)
    born_alive = models.PositiveSmallIntegerField(default=1)
    born_dead = models.PositiveSmallIntegerField(default=0)
    
    # Images
    primary_image = models.ImageField(upload_to=lambing_image_path, null=True, blank=True, help_text="Main image of the lambing event")
    additional_images = models.ManyToManyField('LambingImage', blank=True, related_name='lambing_records')
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Lambing: {self.ewe} on {self.date}"


class LambingImage(models.Model):
    """Model for storing additional lambing event images"""
    image = models.ImageField(upload_to=lambing_image_path)
    caption = models.CharField(max_length=255, blank=True)
    date_added = models.DateField(default=timezone.now)
    
    def __str__(self):
        if hasattr(self, 'lambing_records') and self.lambing_records.exists():
            lambing = self.lambing_records.first()
            return f"Image of lambing: {lambing.ewe} on {lambing.date} - {self.caption}"
        return f"Lambing image - {self.caption}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class HealthRecord(models.Model):
    """Model representing health events for sheep"""
    TYPE_CHOICES = [
        ('VACCINATION', 'Vaccination'),
        ('MEDICATION', 'Medication'),
        ('ILLNESS', 'Illness'),
        ('INJURY', 'Injury'),
        ('PARASITE_TREATMENT', 'Parasite Treatment'),
        ('HOOF_TRIM', 'Hoof Trimming'),
        ('SHEARING', 'Shearing'),
        ('OTHER', 'Other'),
    ]
    
    sheep = models.ForeignKey(Sheep, on_delete=models.CASCADE, related_name='health_records')
    date = models.DateField()
    record_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Details
    treatment = models.CharField(max_length=255, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    administered_by = models.CharField(max_length=100, blank=True)
    
    # Follow-up
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['record_type']),
        ]
    
    def __str__(self):
        return f"{self.get_record_type_display()} for {self.sheep} on {self.date}"
