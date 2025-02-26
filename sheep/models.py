from django.db import models
from django.utils import timezone
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
import uuid
import os


def sheep_image_path(instance, filename):
    """Generate file path for sheep images"""
    # Get the file extension
    ext = filename.split('.')[-1]
    
    # Get tag number safely
    tag = getattr(instance, 'tag_number', None) or 'unknown'
    
    # Create a new filename with sheep's tag number
    new_filename = f"{tag}_{uuid.uuid4().hex}.{ext}"
    
    # Return the complete path
    return os.path.join('sheep_images', new_filename)


def lambing_image_path(instance, filename):
    """Generate file path for lambing record images"""
    # Get the file extension
    ext = filename.split('.')[-1]
    
    # Get tag number safely
    tag = getattr(instance, 'tag_number', None) or 'unknown'
    
    # Get date string
    if hasattr(instance, 'date'):
        # It's a LambingRecord
        date_str = instance.date.strftime('%Y%m%d')
    else:
        # It's a LambingImage or something else
        date_str = timezone.now().strftime('%Y%m%d')
    
    # Create a new filename
    new_filename = f"{tag}_{date_str}_{uuid.uuid4().hex}.{ext}"
    
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
    date_of_birth = models.DateField()
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
    tag_number = models.CharField(max_length=50, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    date_added = models.DateField(default=timezone.now)
    
    def __str__(self):
        if hasattr(self, 'sheep_additional') and self.sheep_additional.exists():
            sheep = self.sheep_additional.first()
            return f"Image of {sheep} - {self.caption}"
        return f"Sheep image - {self.caption}"
    
    def save(self, *args, **kwargs):
        # Skip the tag_number logic if we're explicitly updating only certain fields
        # or if this is being called from a signal handler
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'tag_number' in update_fields:
            return super().save(*args, **kwargs)
            
        # If this image is associated with a sheep and tag_number is not set,
        # get the tag_number from the sheep
        if not self.tag_number:
            # We need to check if the object has been saved first
            if self.pk:
                # Use a direct database query to avoid recursion
                from django.db import connection
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT s.tag_number 
                    FROM sheep_sheep s 
                    JOIN sheep_sheep_additional_images sa ON s.id = sa.sheep_id 
                    WHERE sa.sheepimage_id = %s
                    LIMIT 1
                    """, 
                    [self.pk]
                )
                row = cursor.fetchone()
                if row:
                    self.tag_number = row[0]
        
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
    tag_number = models.CharField(max_length=50, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    date_added = models.DateField(default=timezone.now)
    
    def __str__(self):
        if hasattr(self, 'lambing_records') and self.lambing_records.exists():
            lambing = self.lambing_records.first()
            return f"Image of lambing: {lambing.ewe} on {lambing.date} - {self.caption}"
        return f"Lambing image - {self.caption}"
    
    def save(self, *args, **kwargs):
        # Skip the tag_number logic if we're explicitly updating only certain fields
        # or if this is being called from a signal handler
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'tag_number' in update_fields:
            return super().save(*args, **kwargs)
            
        # If this image is associated with a lambing record and tag_number is not set,
        # get the tag_number from the ewe
        if not self.tag_number:
            # We need to check if the object has been saved first
            if self.pk:
                # Use a direct database query to avoid recursion
                from django.db import connection
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT s.tag_number 
                    FROM sheep_sheep s 
                    JOIN sheep_lambingrecord lr ON s.id = lr.ewe_id 
                    JOIN sheep_lambingrecord_additional_images la ON lr.id = la.lambingrecord_id 
                    WHERE la.lambingimage_id = %s
                    LIMIT 1
                    """, 
                    [self.pk]
                )
                row = cursor.fetchone()
                if row:
                    self.tag_number = row[0]
        
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


# Signal handlers to update tag_number when relationships are created
@receiver(m2m_changed, sender=Sheep.additional_images.through)
def update_sheep_image_tag_number(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Update tag_number in SheepImage when added to a Sheep's additional_images"""
    if action == 'post_add':
        # Use direct SQL to avoid recursion
        from django.db import connection
        
        if not reverse:
            # instance is a Sheep, pk_set contains SheepImage IDs
            if pk_set:
                # Update all images at once using SQL
                cursor = connection.cursor()
                # Only update images where tag_number is empty
                cursor.execute(
                    """
                    UPDATE sheep_sheepimage 
                    SET tag_number = %s 
                    WHERE id IN %s AND (tag_number IS NULL OR tag_number = '')
                    """,
                    [instance.tag_number, tuple(pk_set) if len(pk_set) > 1 else f"({list(pk_set)[0]})"]
                )
        else:
            # instance is a SheepImage, pk_set contains Sheep IDs
            if pk_set and not instance.tag_number:
                # Get the tag_number from the first sheep
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT tag_number FROM sheep_sheep WHERE id = %s
                    """,
                    [list(pk_set)[0]]
                )
                row = cursor.fetchone()
                if row:
                    # Update the image directly using SQL
                    cursor.execute(
                        """
                        UPDATE sheep_sheepimage 
                        SET tag_number = %s 
                        WHERE id = %s
                        """,
                        [row[0], instance.id]
                    )


@receiver(m2m_changed, sender=LambingRecord.additional_images.through)
def update_lambing_image_tag_number(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Update tag_number in LambingImage when added to a LambingRecord's additional_images"""
    if action == 'post_add':
        # Use direct SQL to avoid recursion
        from django.db import connection
        
        if not reverse:
            # instance is a LambingRecord, pk_set contains LambingImage IDs
            if pk_set:
                # Get the ewe's tag_number
                tag_number = instance.ewe.tag_number
                
                # Update all images at once using SQL
                cursor = connection.cursor()
                # Only update images where tag_number is empty
                cursor.execute(
                    """
                    UPDATE sheep_lambingimage 
                    SET tag_number = %s 
                    WHERE id IN %s AND (tag_number IS NULL OR tag_number = '')
                    """,
                    [tag_number, tuple(pk_set) if len(pk_set) > 1 else f"({list(pk_set)[0]})"]
                )
        else:
            # instance is a LambingImage, pk_set contains LambingRecord IDs
            if pk_set and not instance.tag_number:
                # Get the tag_number from the ewe of the first lambing record
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT s.tag_number 
                    FROM sheep_sheep s 
                    JOIN sheep_lambingrecord lr ON s.id = lr.ewe_id 
                    WHERE lr.id = %s
                    """,
                    [list(pk_set)[0]]
                )
                row = cursor.fetchone()
                if row:
                    # Update the image directly using SQL
                    cursor.execute(
                        """
                        UPDATE sheep_lambingimage 
                        SET tag_number = %s 
                        WHERE id = %s
                        """,
                        [row[0], instance.id]
                    )
