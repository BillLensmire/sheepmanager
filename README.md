# Sheep Manager

A Django-based application for managing sheep flocks, breeding records, and health tracking.

## Features

- Track individual sheep with detailed information
- Record breeding events between ewes and rams
- Document lambing events and offspring
- Maintain health records for each sheep
- Comprehensive admin interface for data management

## Models

### Breed
- Represents different sheep breeds
- Stores name and description

### Sheep
- Core model for individual sheep
- Tracks identification (tag number, name, UUID)
- Records basic information (gender, date of birth, breed)
- Stores physical characteristics (weight, color, markings)
- Maintains lineage information (mother, father)
- Tracks status (active, sold, deceased, culled)

### BreedingRecord
- Documents breeding events between ewes and rams
- Tracks breeding dates and status
- Links to lambing events

### LambingRecord
- Records lambing events (birth of lambs)
- Tracks number of lambs born (total, alive, dead)
- Documents complications and assistance provided

### HealthRecord
- Maintains health-related events for each sheep
- Supports various record types (vaccination, medication, illness, etc.)
- Tracks treatments, dosages, and follow-up requirements

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Apply migrations: `python manage.py migrate`
4. Create a superuser: `python manage.py createsuperuser`
5. Run the development server: `python manage.py runserver`
6. Access the admin interface at http://localhost:8000/admin/

## Usage

1. First, add breeds through the admin interface
2. Add individual sheep with their details
3. Record breeding events between ewes and rams
4. Document lambing events and link them to breeding records
5. Maintain health records for each sheep

## License

This project is licensed under the MIT License - see the LICENSE file for details.
