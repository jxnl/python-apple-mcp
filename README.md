# Python Apple MCP (Model Context Protocol)

[![smithery badge](https://smithery.ai/badge/@jxnl/python-apple-mcp)](https://smithery.ai/server/@jxnl/python-apple-mcp)

A Python implementation of the server that handles interactions with macOS applications such as Contacts, Notes, Mail, Messages, Reminders, Calendar, and Maps using FastMCP.

## Features

- Interact with macOS native applications through AppleScript
- Asynchronous operations for better performance
- Comprehensive error handling
- Type-safe interfaces using Pydantic models
- Extensive test coverage
- Modular design for easy extension

## Supported Applications

- Contacts
- Notes
- Mail
- Messages
- Reminders
- Calendar
- Maps

## Installation

### Installing via Smithery

To install Python Apple MCP for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@jxnl/python-apple-mcp):

```bash
npx -y @smithery/cli install @jxnl/python-apple-mcp --client claude
```

### Installing via Git

1. Clone the repository:
```bash
git clone https://github.com/jxnl/python-apple-mcp.git
cd python-apple-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install test dependencies (optional):
```bash
pip install -r requirements-test.txt
```

## Usage

### Basic Example

```python
from apple_mcp import FastMCP, Context

# Initialize FastMCP server
mcp = FastMCP("Apple MCP")

# Use the tools
@mcp.tool()
def find_contact(name: str) -> List[Contact]:
    """Search for contacts by name"""
    # Implementation here
    pass

# Run the server
if __name__ == "__main__":
    mcp.run()
```

### Using Individual Modules

```python
from utils.contacts import ContactsModule
from utils.notes import NotesModule

# Initialize modules
contacts = ContactsModule()
notes = NotesModule()

# Use the modules
async def main():
    # Find a contact
    contact = await contacts.find_contact("John")
    
    # Create a note
    await notes.create_note(
        title="Meeting Notes",
        body="Discussion points...",
        folder_name="Work"
    )

# Run the async code
import asyncio
asyncio.run(main())
```

## Testing

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=utils tests/
```

Run specific test file:
```bash
pytest tests/test_contacts.py
```

## API Documentation

### Contacts Module

- `find_contact(name: str) -> List[Contact]`: Search for contacts by name
- `get_all_contacts() -> List[Contact]`: Get all contacts
- `create_contact(name: str, phones: List[str]) -> Contact`: Create a new contact

### Notes Module

- `find_note(query: str) -> List[Note]`: Search for notes
- `create_note(title: str, body: str, folder_name: str) -> Note`: Create a new note
- `get_all_notes() -> List[Note]`: Get all notes

### Mail Module

- `send_email(to: str, subject: str, body: str) -> str`: Send an email
- `search_emails(query: str) -> List[Email]`: Search emails
- `get_unread_mails() -> List[Email]`: Get unread emails

### Messages Module

- `send_message(to: str, content: str) -> bool`: Send an iMessage
- `read_messages(phone_number: str) -> List[Message]`: Read messages
- `schedule_message(to: str, content: str, scheduled_time: str) -> Dict`: Schedule a message

### Reminders Module

- `create_reminder(name: str, list_name: str, notes: str, due_date: str) -> Dict`: Create a reminder
- `search_reminders(query: str) -> List[Dict]`: Search reminders
- `get_all_reminders() -> List[Dict]`: Get all reminders

### Calendar Module

- `create_event(title: str, start_date: str, end_date: str, location: str, notes: str) -> Dict`: Create an event
- `search_events(query: str) -> List[Dict]`: Search events
- `get_events() -> List[Dict]`: Get all events

### Maps Module

- `search_locations(query: str) -> List[Location]`: Search for locations
- `get_directions(from_address: str, to_address: str, transport_type: str) -> str`: Get directions
- `save_location(name: str, address: str) -> Dict`: Save a location to favorites

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
