"""Message module for interacting with Apple Messages."""

import logging
from typing import Dict, List, Any
from datetime import datetime

from .applescript import (
    run_applescript_async,
    AppleScriptError,
    escape_string,
    parse_applescript_record,
    parse_applescript_list
)

logger = logging.getLogger(__name__)

class MessageModule:
    """Module for interacting with Apple Messages"""
    
    async def check_messages_access(self) -> bool:
        """Check if Messages app is accessible"""
        try:
            script = '''
            try
                tell application "Messages"
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
            logger.error(f"Cannot access Messages app: {e}")
            return False
    
    async def send_message(self, phone_number: str, message: str) -> bool:
        """Send a message to a phone number"""
        safe_phone = escape_string(phone_number)
        safe_message = escape_string(message)
        script = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{safe_phone}" of targetService
                send "{safe_message}" to targetBuddy
                return "SUCCESS:Message sent"
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            return result.startswith("SUCCESS:")
        except AppleScriptError as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def read_messages(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Read messages from a specific contact"""
        limit = max(1, min(int(limit), 1000))
        safe_phone = escape_string(phone_number)
        script = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{safe_phone}" of targetService
                set msgs to {{}}
                set convMessages to messages of chat targetBuddy
                repeat with i from 1 to {limit}
                    if i > count of convMessages then exit repeat
                    set m to item i of convMessages
                    set end of msgs to {{
                        content:text of m,
                        sender:sender of m,
                        date:date sent of m,
                        is_from_me:(sender of m = me)
                    }}
                end repeat
                return msgs as text
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            messages = parse_applescript_list(result)
            return [parse_applescript_record(msg) for msg in messages]
        except AppleScriptError as e:
            logger.error(f"Error reading messages: {e}")
            return []
    
    async def schedule_message(self, phone_number: str, message: str, scheduled_time: str) -> Dict[str, Any]:
        """Schedule a message to be sent later"""
        safe_phone = escape_string(phone_number)
        safe_message = escape_string(message)
        safe_time = escape_string(scheduled_time)
        script = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{safe_phone}" of targetService
                set scheduledTime to date "{safe_time}"
                send "{safe_message}" to targetBuddy at scheduledTime
                return "SUCCESS:Message scheduled for {safe_time}"
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", ""),
                "scheduled": {
                    "to": phone_number,
                    "content": message,
                    "scheduled_time": scheduled_time
                } if success else None
            }
        except AppleScriptError as e:
            logger.error(f"Error scheduling message: {e}")
            return {
                "success": False,
                "message": str(e),
                "scheduled": None
            }
    
    async def get_unread_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get unread messages"""
        limit = max(1, min(int(limit), 1000))
        script = f'''
            tell application "Messages"
                set unreadMsgs to {{}}
                set allChats to every chat
                repeat with c in allChats
                    if unread count of c > 0 then
                        set msgs to messages of c
                        repeat with i from 1 to {limit}
                            if i > count of msgs then exit repeat
                            set m to item i of msgs
                            if read status of m is false then
                                set end of unreadMsgs to {{
                                    content:text of m,
                                    sender:sender of m,
                                    date:date sent of m,
                                    is_from_me:(sender of m = me)
                                }}
                            end if
                        end repeat
                    end if
                end repeat
                return unreadMsgs as text
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            messages = parse_applescript_list(result)
            return [parse_applescript_record(msg) for msg in messages]
        except AppleScriptError as e:
            logger.error(f"Error getting unread messages: {e}")
            return []