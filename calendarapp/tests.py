from django.test import TestCase
from .models import Event
from .views import EventManager
from datetime import datetime


# Create your tests here.

# created tests for the events "creating, deleting, edititng"
class EventTests(TestCase):
    def setUp(self):
        # Set up data for the tests
        self.event_date = datetime(2023, 12, 25).date()
        self.event_name = "Test Event"
        self.event_description = "This is a test event."
        self.manager = EventManager()

    def test_create_event(self):
        # Test creating an event
        self.manager.create_event(self.event_name, self.event_date, self.event_description)
        event = Event.objects.first()  # Retrieve the first event from the database
        self.assertEqual(event.name, self.event_name)
        self.assertEqual(event.date, self.event_date)
        self.assertEqual(event.description, self.event_description)

    def test_create_event_without_description(self):
        # Test creating an event without a description
        self.manager.create_event(self.event_name, self.event_date)
        event = Event.objects.first()
        self.assertEqual(event.description, "")

    def test_delete_event(self):
        # Test deleting an event
        self.manager.create_event(self.event_name, self.event_date, self.event_description)
        event = Event.objects.first()
        self.manager.delete_event(event.id)
        self.assertEqual(Event.objects.count(), 0)

    def test_edit_event_name(self):
        # Test editing an event's name
        self.manager.create_event(self.event_name, self.event_date, self.event_description)
        event = Event.objects.first()
        new_name = "Updated Event Name"
        self.manager.edit_event(event.id, new_name=new_name)
        updated_event = Event.objects.get(id=event.id)
        self.assertEqual(updated_event.name, new_name)

    def test_edit_event_date(self):
        # Test editing an event's date
        self.manager.create_event(self.event_name, self.event_date, self.event_description)
        event = Event.objects.first()
        new_date = datetime(2024, 1, 1).date()
        self.manager.edit_event(event.id, new_date=new_date)
        updated_event = Event.objects.get(id=event.id)
        self.assertEqual(updated_event.date, new_date)

    def test_edit_event_description(self):
        # Test editing an event's description
        self.manager.create_event(self.event_name, self.event_date, self.event_description)
        event = Event.objects.first()
        new_description = "Updated description."
        self.manager.edit_event(event.id, new_description=new_description)
        updated_event = Event.objects.get(id=event.id)
        self.assertEqual(updated_event.description, new_description)

    def test_edit_event_description_to_empty(self):
        # Test editing an event's description to empty
        self.manager.create_event(self.event_name, self.event_date, self.event_description)
        event = Event.objects.first()
        self.manager.edit_event(event.id, new_description="")
        updated_event = Event.objects.get(id=event.id)
        self.assertEqual(updated_event.description, "")

    def test_list_events(self):
        # Test listing events
        self.manager.create_event(self.event_name, self.event_date, self.event_description)
        self.manager.create_event("Another Event", datetime(2023, 11, 15).date())
        events = Event.objects.all()
        self.assertEqual(events.count(), 2)

    def test_list_events_when_empty(self):
        # Test listing events when no events exist
        events = Event.objects.all()
        self.assertEqual(events.count(), 0)

