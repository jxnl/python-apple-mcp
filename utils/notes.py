"""Notes module for interacting with Apple Notes."""

import logging
from typing import Dict, List, Any

from .applescript import (
    run_applescript_async,
    AppleScriptError,
    escape_string,
    format_applescript_value,
    parse_applescript_record,
    parse_applescript_list
)

logger = logging.getLogger(__name__)

class NotesModule:
    """Module for interacting with Apple Notes"""
    
    async def check_notes_access(self) -> bool:
        """Check if Notes app is accessible"""
        try:
            script = '''
            try
                tell application "Notes"
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
            logger.error(f"Cannot access Notes app: {e}")
            return False
    
    async def find_note(self, search_text: str) -> List[Dict[str, Any]]:
        """Find notes containing the search text"""
        safe_text = escape_string(search_text)
        script = f'''
            tell application "Notes"
                set matchingNotes to {{}}
                repeat with n in every note
                    if (body of n contains "{safe_text}") or (name of n contains "{safe_text}") then
                        set noteData to {{name:name of n, body:body of n}}
                        copy noteData to end of matchingNotes
                    end if
                end repeat
                return matchingNotes
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            notes = parse_applescript_list(result)
            parsed_notes = []
            
            for note in notes:
                note_dict = parse_applescript_record(note)
                # Normalize keys to ensure consistency with create_note return
                if "name" in note_dict:
                    note_dict["title"] = note_dict["name"]
                if "body" in note_dict:
                    note_dict["content"] = note_dict["body"]
                parsed_notes.append(note_dict)
            
            return parsed_notes
        except AppleScriptError as e:
            logger.error(f"Error finding notes: {e}")
            return []
    
    async def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes"""
        script = '''
            tell application "Notes"
                set allNotes to {}
                repeat with n in every note
                    set end of allNotes to {
                        title:name of n,
                        content:body of n,
                        folder:name of container of n,
                        creation_date:creation date of n,
                        modification_date:modification date of n
                    }
                end repeat
                return allNotes as text
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            notes = parse_applescript_list(result)
            return [parse_applescript_record(note) for note in notes]
        except AppleScriptError as e:
            logger.error(f"Error getting all notes: {e}")
            return []
    
    async def create_note(self, title: str, body: str, folder_name: str = 'Notes') -> Dict[str, Any]:
        """Create a new note"""
        safe_title = escape_string(title)
        safe_body = escape_string(body)
        safe_folder = escape_string(folder_name)
        script = f'''
            tell application "Notes"
                tell account "iCloud"
                    if not (exists folder "{safe_folder}") then
                        make new folder with properties {{name:"{safe_folder}"}}
                    end if
                    tell folder "{safe_folder}"
                        make new note with properties {{name:"{safe_title}", body:"{safe_body}"}}
                        return "SUCCESS:Created note '{safe_title}' in folder '{safe_folder}'"
                    end tell
                end tell
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", ""),
                "note": {
                    "title": title,
                    "content": body,
                    "folder": folder_name
                } if success else None
            }
        except AppleScriptError as e:
            logger.error(f"Error creating note: {e}")
            return {
                "success": False,
                "message": str(e),
                "note": None
            }