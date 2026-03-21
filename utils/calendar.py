"""Calendar module for interacting with Apple Calendar."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .applescript import (
    run_applescript_async,
    AppleScriptError,
    escape_string,
    format_applescript_value,
    parse_applescript_record,
    parse_applescript_list
)

logger = logging.getLogger(__name__)

class CalendarModule:
    """Module for interacting with Apple Calendar"""
    
    async def check_calendar_access(self) -> bool:
        """Check if Calendar app is accessible"""
        try:
            script = '''
            try
                tell application "Calendar"
                    get name
                    return true
                end tell
            on error
                return false
            end try
            '''
            
            result = await run_applescript_async(script)
            return result.lower() == 'true'
        except Exception as e:
            logger.error(f"Cannot access Calendar app: {e}")
            return False
    
    async def search_events(self, search_text: str, limit: Optional[int] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for calendar events matching text"""
        if not from_date:
            from_date = datetime.now().strftime("%Y-%m-%d")
        if not to_date:
            to_date = (datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=7)).strftime("%Y-%m-%d")

        safe_text = escape_string(search_text)
        safe_from = escape_string(from_date)
        safe_to = escape_string(to_date)

        script = f'''
            tell application "Calendar"
                set matchingEvents to {{}}
                set searchStart to date "{safe_from}"
                set searchEnd to date "{safe_to}"
                set foundEvents to every event whose summary contains "{safe_text}" and start date is greater than or equal to searchStart and start date is less than or equal to searchEnd
                repeat with e in foundEvents
                    set end of matchingEvents to {{
                        title:summary of e,
                        start_date:start date of e,
                        end_date:end date of e,
                        location:location of e,
                        notes:description of e,
                        calendar:name of calendar of e
                    }}
                end repeat
                return matchingEvents as text
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            events = parse_applescript_list(result)
            
            if limit:
                events = events[:limit]
                
            return [parse_applescript_record(event) for event in events]
        except AppleScriptError as e:
            logger.error(f"Error searching events: {e}")
            return []
    
    async def open_event(self, event_id: str) -> Dict[str, Any]:
        """Open a specific calendar event"""
        safe_id = escape_string(event_id)
        script = f'''
            tell application "Calendar"
                try
                    set theEvent to first event whose uid is "{safe_id}"
                    show theEvent
                    return "Opened event: " & summary of theEvent
                on error
                    return "ERROR: Event not found"
                end try
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            success = not result.startswith("ERROR:")
            return {
                "success": success,
                "message": result.replace("ERROR: ", "") if not success else result
            }
        except AppleScriptError as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    async def get_events(self, limit: Optional[int] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get calendar events in a date range"""
        if not from_date:
            from_date = datetime.now().strftime("%Y-%m-%d")
        if not to_date:
            to_date = (datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=7)).strftime("%Y-%m-%d")

        safe_from = escape_string(from_date)
        safe_to = escape_string(to_date)

        script = f'''
            tell application "Calendar"
                set allEvents to {{}}
                set searchStart to date "{safe_from}"
                set searchEnd to date "{safe_to}"
                set foundEvents to every event whose start date is greater than or equal to searchStart and start date is less than or equal to searchEnd
                repeat with e in foundEvents
                    set end of allEvents to {{
                        title:summary of e,
                        start_date:start date of e,
                        end_date:end date of e,
                        location:location of e,
                        notes:description of e,
                        calendar:name of calendar of e
                    }}
                end repeat
                return allEvents as text
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            events = parse_applescript_list(result)
            
            if limit:
                events = events[:limit]
                
            return [parse_applescript_record(event) for event in events]
        except AppleScriptError as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    async def create_event(self, title: str, start_date: datetime, end_date: datetime, location: str = None, notes: str = None, calendar_name: str = None) -> Dict[str, Any]:
        """Create a new calendar event"""
        # Using a simpler approach for Calendar that is more likely to work
        formatted_start = start_date.strftime("%Y-%m-%d %H:%M:%S")
        formatted_end = end_date.strftime("%Y-%m-%d %H:%M:%S")

        safe_title = escape_string(title)
        safe_start = escape_string(formatted_start)
        safe_end = escape_string(formatted_end)

        # Create a simpler script that just adds an event to the default calendar
        script = f'''
            tell application "Calendar"
                try
                    tell application "Calendar"
                        tell (first calendar whose name is "Calendar")
                            make new event at end with properties {{summary:"{safe_title}", start date:(date "{safe_start}"), end date:(date "{safe_end}")}}
                            return "SUCCESS:Event created successfully"
                        end tell
                    end tell
                on error errMsg
                    return "ERROR:" & errMsg
                end try
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", "")
            }
        except AppleScriptError as e:
            logger.error(f"Error creating event: {e}")
            return {
                "success": False,
                "message": str(e)
            }