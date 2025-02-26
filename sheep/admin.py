from django.contrib import admin
from .models import Breed, Sheep, BreedingRecord, LambingRecord, HealthRecord, SheepImage, LambingImage


class SheepImageInline(admin.TabularInline):
    model = SheepImage.sheep_additional.through
    extra = 1
    verbose_name = "Additional Image"
    verbose_name_plural = "Additional Images"


class LambingImageInline(admin.TabularInline):
    model = LambingImage.lambing_records.through
    extra = 1
    verbose_name = "Additional Image"
    verbose_name_plural = "Additional Images"


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')


@admin.register(Sheep)
class SheepAdmin(admin.ModelAdmin):
    list_display = ('tag_number', 'name', 'gender', 'breed', 'date_of_birth', 'status')
    list_filter = ('gender', 'breed', 'status')
    search_fields = ('tag_number', 'name')
    fieldsets = (
        ('Identification', {
            'fields': ('tag_number', 'name', 'uuid')
        }),
        ('Basic Information', {
            'fields': ('gender', 'date_of_birth', 'breed')
        }),
        ('Physical Characteristics', {
            'fields': ('weight_birth', 'weight_current', 'color', 'markings')
        }),
        ('Images', {
            'fields': ('primary_image',)
        }),
        ('Lineage', {
            'fields': ('mother', 'father')
        }),
        ('Status', {
            'fields': ('status', 'date_acquired', 'date_removed', 'removal_reason')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    autocomplete_fields = ['mother', 'father', 'breed']
    readonly_fields = ('uuid',)
    inlines = [SheepImageInline]


class LambingInline(admin.TabularInline):
    model = LambingRecord
    extra = 0
    fields = ('date', 'total_born', 'born_alive', 'born_dead', 'assisted')


@admin.register(BreedingRecord)
class BreedingRecordAdmin(admin.ModelAdmin):
    list_display = ('ewe', 'ram', 'date_started', 'status', 'expected_lambing_date')
    list_filter = ('status',)
    search_fields = ('ewe__tag_number', 'ewe__name', 'ram__tag_number', 'ram__name')
    autocomplete_fields = ['ewe', 'ram']
    inlines = [LambingInline]


@admin.register(LambingRecord)
class LambingRecordAdmin(admin.ModelAdmin):
    list_display = ('ewe', 'date', 'total_born', 'born_alive', 'born_dead', 'assisted')
    list_filter = ('assisted',)
    search_fields = ('ewe__tag_number', 'ewe__name')
    autocomplete_fields = ['ewe', 'breeding_record']
    fieldsets = (
        (None, {
            'fields': ('breeding_record', 'ewe', 'date')
        }),
        ('Lambing Details', {
            'fields': ('assisted', 'complications', 'total_born', 'born_alive', 'born_dead')
        }),
        ('Images', {
            'fields': ('primary_image',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    inlines = [LambingImageInline]


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('sheep', 'date', 'record_type', 'treatment', 'requires_followup')
    list_filter = ('record_type', 'requires_followup')
    search_fields = ('sheep__tag_number', 'sheep__name', 'treatment')
    autocomplete_fields = ['sheep']


@admin.register(SheepImage)
class SheepImageAdmin(admin.ModelAdmin):
    list_display = ('caption', 'date_added')
    search_fields = ('caption', 'date_added')
    exclude = ('sheep_additional',)


@admin.register(LambingImage)
class LambingImageAdmin(admin.ModelAdmin):
    list_display = ('caption', 'date_added')
    search_fields = ('caption', 'date_added')
    exclude = ('lambing_records',)
