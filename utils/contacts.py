"""Contacts module for interacting with Apple Contacts."""

import logging
from typing import Dict, List, Any, Optional

from .applescript import (
    run_applescript_async,
    AppleScriptError,
    escape_string,
    parse_applescript_record,
    parse_applescript_list
)

logger = logging.getLogger(__name__)

class ContactsModule:
    """Module for interacting with Apple Contacts"""
    
    async def check_contacts_access(self) -> bool:
        """Check if Contacts app is accessible"""
        try:
            script = '''
            try
                tell application "Contacts"
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
            logger.error(f"Cannot access Contacts app: {e}")
            return False
    
    async def find_number(self, name: str) -> List[str]:
        """Find phone numbers for a contact"""
        safe_name = escape_string(name)
        script = f'''
            tell application "Contacts"
                set matchingPeople to (every person whose name contains "{safe_name}")
                set phoneNumbers to {{}}
                repeat with p in matchingPeople
                    repeat with ph in phones of p
                        copy value of ph to end of phoneNumbers
                    end repeat
                end repeat
                return phoneNumbers as text
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            return parse_applescript_list(result)
        except AppleScriptError as e:
            logger.error(f"Error finding phone numbers: {e}")
            return []
    
    async def get_all_numbers(self) -> Dict[str, List[str]]:
        """Get all contacts with their phone numbers"""
        script = '''
            tell application "Contacts"
                set allContacts to {}
                repeat with p in every person
                    set phones to {}
                    repeat with ph in phones of p
                        copy value of ph to end of phones
                    end repeat
                    if length of phones is greater than 0 then
                        set end of allContacts to {name:name of p, phones:phones}
                    end if
                end repeat
                return allContacts as text
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            contacts = parse_applescript_list(result)
            
            # Convert to dictionary format
            contact_dict = {}
            for contact in contacts:
                contact_data = parse_applescript_record(contact)
                contact_dict[contact_data['name']] = contact_data.get('phones', [])
            
            return contact_dict
        except AppleScriptError as e:
            logger.error(f"Error getting all contacts: {e}")
            return {}
    
    async def find_contact_by_phone(self, phone_number: str) -> Optional[str]:
        """Find a contact's name by phone number"""
        safe_phone = escape_string(phone_number)
        script = f'''
            tell application "Contacts"
                set foundName to missing value
                repeat with p in every person
                    repeat with ph in phones of p
                        if value of ph contains "{safe_phone}" then
                            set foundName to name of p
                            exit repeat
                        end if
                    end repeat
                    if foundName is not missing value then
                        exit repeat
                    end if
                end repeat
                return foundName
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            if result and result.lower() != "missing value":
                return result
            return None
        except AppleScriptError as e:
            logger.error(f"Error finding contact by phone: {e}")
            return None