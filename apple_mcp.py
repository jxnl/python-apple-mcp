#!/usr/bin/env python3
"""
Python Apple MCP (Model Context Protocol) Server

This is a Python implementation of the server that handles interactions with
macOS applications such as Contacts, Notes, Mail, Messages, Reminders, 
Calendar, and Maps using FastMCP.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP
from utils.contacts import ContactsModule
from utils.notes import NotesModule
from utils.message import MessageModule
from utils.mail import MailModule
from utils.reminders import RemindersModule
from utils.calendar import CalendarModule
from utils.maps import MapsModule

# Initialize FastMCP server
mcp = FastMCP(
    "Apple MCP",
    dependencies=[
        "pydantic>=2.0.0",
    ]
)

# Initialize utility modules
contacts_module = ContactsModule()
notes_module = NotesModule()
message_module = MessageModule()
mail_module = MailModule()
reminders_module = RemindersModule()
calendar_module = CalendarModule()
maps_module = MapsModule()

# Models for request/response types
class Contact(BaseModel):
    name: str
    phones: List[str]

class Note(BaseModel):
    title: str
    content: str
    folder: Optional[str] = "Claude"

class Message(BaseModel):
    to: str
    content: str
    scheduled_time: Optional[str] = None

class Email(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None

class Reminder(BaseModel):
    title: str
    notes: Optional[str] = None
    due_date: Optional[str] = None
    list_name: Optional[str] = None

class CalendarEvent(BaseModel):
    title: str
    start_date: str
    end_date: str
    location: Optional[str] = None
    notes: Optional[str] = None
    is_all_day: bool = False
    calendar_name: Optional[str] = None

class Location(BaseModel):
    name: str
    address: str

# Contacts Tools
@mcp.tool()
async def find_contact(name: Optional[str] = None) -> List[Contact]:
    """Search for contacts by name. If no name is provided, returns all contacts."""
    if name:
        phones = await contacts_module.find_number(name)
        return [Contact(name=name, phones=phones)]
    else:
        contacts_dict = await contacts_module.get_all_numbers()
        return [Contact(name=name, phones=phones) for name, phones in contacts_dict.items()]

# Notes Tools
@mcp.tool()
async def create_note(note: Note) -> str:
    """Create a new note in Apple Notes"""
    return await notes_module.create_note(note.title, note.content, note.folder)

@mcp.tool()
async def search_notes(query: str) -> List[Note]:
    """Search for notes containing the given text"""
    notes = await notes_module.search_notes(query)
    return [Note(title=note['title'], content=note['content']) for note in notes]

# Messages Tools
@mcp.tool()
async def send_message(message: Message) -> str:
    """Send an iMessage"""
    return await message_module.send_message(message.to, message.content, message.scheduled_time)

@mcp.tool()
async def read_messages(phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Read recent messages from a specific contact"""
    return await message_module.read_messages(phone_number, limit)

# Mail Tools
@mcp.tool()
async def send_email(email: Email) -> str:
    """Send an email using Apple Mail"""
    return await mail_module.send_email(
        to=email.to,
        subject=email.subject,
        body=email.body,
        cc=email.cc,
        bcc=email.bcc
    )

@mcp.tool()
async def search_emails(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search emails containing the given text"""
    return await mail_module.search_emails(query, limit)

# Reminders Tools
@mcp.tool()
async def create_reminder(reminder: Reminder) -> str:
    """Create a new reminder"""
    return await reminders_module.create_reminder(
        title=reminder.title,
        notes=reminder.notes,
        due_date=reminder.due_date,
        list_name=reminder.list_name
    )

@mcp.tool()
async def search_reminders(query: str) -> List[Dict[str, Any]]:
    """Search for reminders containing the given text"""
    return await reminders_module.search_reminders(query)

# Calendar Tools
@mcp.tool()
async def create_event(event: CalendarEvent) -> str:
    """Create a new calendar event"""
    return await calendar_module.create_event(
        title=event.title,
        start_date=event.start_date,
        end_date=event.end_date,
        location=event.location,
        notes=event.notes,
        is_all_day=event.is_all_day,
        calendar_name=event.calendar_name
    )

@mcp.tool()
async def search_events(query: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for calendar events"""
    if not from_date:
        from_date = datetime.now().strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=7)).strftime("%Y-%m-%d")
    
    return await calendar_module.search_events(query, from_date, to_date)

# Maps Tools
@mcp.tool()
async def search_locations(query: str, limit: int = 5) -> List[Location]:
    """Search for locations in Apple Maps"""
    locations = await maps_module.search_locations(query, limit)
    return [Location(name=loc['name'], address=loc['address']) for loc in locations]

@mcp.tool()
async def get_directions(from_address: str, to_address: str, transport_type: str = "driving") -> str:
    """Get directions between two locations"""
    return await maps_module.get_directions(from_address, to_address, transport_type)

if __name__ == "__main__":
    mcp.run()