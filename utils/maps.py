"""
Maps utility module for interacting with Apple Maps.

This module provides functions to perform various operations with Apple Maps
like searching for locations, saving locations, getting directions, etc.
"""

import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union

from .applescript import (
    run_applescript_async,
    AppleScriptError,
    escape_string,
    format_applescript_value,
    parse_applescript_record,
    parse_applescript_list
)

logger = logging.getLogger(__name__)

class MapsModule:
    """Module for interacting with Apple Maps"""
    
    async def check_maps_access(self) -> bool:
        """
        Check if Maps app is accessible
        
        Returns:
            True if Maps app is accessible, False otherwise
        """
        try:
            script = '''
            try
                tell application "Maps"
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
            logger.error(f"Cannot access Maps app: {e}")
            return False
    
    async def search_locations(self, query: str) -> Dict[str, Any]:
        """Search for locations in Apple Maps"""
        safe_query = escape_string(query)
        script = f'''
            tell application "Maps"
                try
                    activate
                    search "{safe_query}"
                    delay 1
                    set locations to {{}}
                    set searchResults to selected location
                    if searchResults is not missing value then
                        set locName to name of searchResults
                        set locAddress to formatted address of searchResults
                        if locAddress is missing value then
                            set locAddress to "Unknown"
                        end if
                        set locationInfo to {{name:locName, address:locAddress}}
                        set end of locations to locationInfo
                    end if
                    return locations
                on error errMsg
                    return "ERROR:" & errMsg
                end try
            end tell
        '''
        
        try:
            result = await run_applescript_async(script)
            if result.startswith("ERROR:"):
                logger.error(f"Error in AppleScript: {result}")
                return {
                    "success": False,
                    "message": result.replace("ERROR:", ""),
                    "locations": []
                }
                
            locations = parse_applescript_list(result)
            return {
                "success": True,
                "locations": [parse_applescript_record(loc) for loc in locations]
            }
        except AppleScriptError as e:
            logger.error(f"Error searching locations: {e}")
            return {
                "success": False,
                "message": str(e),
                "locations": []
            }
    
    async def save_location(self, name: str, address: str) -> Dict[str, Any]:
        """
        Save a location to favorites
        
        Args:
            name: Name of the location
            address: Address to save
            
        Returns:
            A dictionary containing the result of the operation
        """
        try:
            if not await self.check_maps_access():
                return {
                    "success": False,
                    "message": "Cannot access Maps app. Please grant access in System Settings > Privacy & Security > Automation."
                }
            
            logger.info(f"Saving location: {name} at {address}")

            safe_name = escape_string(name)
            safe_address = escape_string(address)

            script = f'''
                tell application "Maps"
                    activate

                    -- First search for the location
                    search "{safe_address}"

                    -- Wait for search to complete
                    delay 1

                    -- Try to get the current location
                    set foundLocation to selected location

                    if foundLocation is not missing value then
                        -- Add to favorites
                        add to favorites foundLocation with properties {{name:"{safe_name}"}}
                        
                        -- Return success with location details
                        set locationAddress to formatted address of foundLocation
                        if locationAddress is missing value then
                            set locationAddress to "{safe_address}"
                        end if
                        
                        return "SUCCESS:Added \\"" & "{safe_name}" & "\\" to favorites"
                    else
                        return "ERROR:Could not find location for \\"" & "{safe_address}" & "\\""
                    end if
                end tell
            '''
            
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", "")
            }
        except Exception as e:
            logger.error(f"Error saving location: {e}")
            return {
                "success": False,
                "message": f"Error saving location: {str(e)}"
            }
    
    async def get_directions(
        self, 
        from_address: str, 
        to_address: str, 
        transport_type: str = 'driving'
    ) -> Dict[str, Any]:
        """
        Get directions between two locations
        
        Args:
            from_address: Starting address
            to_address: Destination address
            transport_type: Type of transport to use (default: 'driving')
            
        Returns:
            A dictionary containing the result of the operation
        """
        try:
            if not await self.check_maps_access():
                return {
                    "success": False,
                    "message": "Cannot access Maps app. Please grant access in System Settings > Privacy & Security > Automation."
                }
            
            logger.info(f"Getting directions from {from_address} to {to_address} by {transport_type}")

            safe_from = escape_string(from_address)
            safe_to = escape_string(to_address)
            safe_transport = escape_string(transport_type)

            script = f'''
                tell application "Maps"
                    activate

                    -- Ask for directions
                    get directions from "{safe_from}" to "{safe_to}" by "{safe_transport}"

                    return "SUCCESS:Displaying directions from \\"" & "{safe_from}" & "\\" to \\"" & "{safe_to}" & "\\" by {safe_transport}"
                end tell
            '''
            
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", ""),
                "route": {
                    "from": from_address,
                    "to": to_address,
                    "transport_type": transport_type
                } if success else None
            }
        except Exception as e:
            logger.error(f"Error getting directions: {e}")
            return {
                "success": False,
                "message": f"Error getting directions: {str(e)}"
            }
    
    async def drop_pin(self, name: str, address: str) -> Dict[str, Any]:
        """
        Create a pin at a specified location
        
        Args:
            name: Name of the pin
            address: Location address
            
        Returns:
            A dictionary containing the result of the operation
        """
        try:
            if not await self.check_maps_access():
                return {
                    "success": False,
                    "message": "Cannot access Maps app. Please grant access in System Settings > Privacy & Security > Automation."
                }
            
            logger.info(f"Creating pin at {address} with name {name}")

            safe_name = escape_string(name)
            safe_address = escape_string(address)

            script = f'''
                tell application "Maps"
                    activate

                    -- Search for the location
                    search "{safe_address}"

                    -- Wait for search to complete
                    delay 1

                    -- Try to get the current location
                    set foundLocation to selected location

                    if foundLocation is not missing value then
                        -- Drop pin (note: this is a user interface action)
                        return "SUCCESS:Location found. Right-click and select 'Drop Pin' to create a pin named \\"" & "{safe_name}" & "\\""
                    else
                        return "ERROR:Could not find location for \\"" & "{safe_address}" & "\\""
                    end if
                end tell
            '''
            
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", "")
            }
        except Exception as e:
            logger.error(f"Error dropping pin: {e}")
            return {
                "success": False,
                "message": f"Error dropping pin: {str(e)}"
            }
    
    async def list_guides(self) -> Dict[str, Any]:
        """
        List all guides in Apple Maps
        
        Returns:
            A dictionary containing guides information
        """
        try:
            if not await self.check_maps_access():
                return {
                    "success": False,
                    "message": "Cannot access Maps app. Please grant access in System Settings > Privacy & Security > Automation."
                }
            
            logger.info("Listing guides from Maps")
            
            script = '''
                tell application "Maps"
                    activate
                    
                    -- Open guides view
                    open location "maps://?show=guides"
                    
                    return "SUCCESS:Opened guides view in Maps"
                end tell
            '''
            
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", ""),
                "guides": []  # Note: Currently no direct AppleScript access to guides
            }
        except Exception as e:
            logger.error(f"Error listing guides: {e}")
            return {
                "success": False,
                "message": f"Error listing guides: {str(e)}"
            }
    
    async def add_to_guide(self, location_address: str, guide_name: str) -> Dict[str, Any]:
        """
        Add a location to a specific guide
        
        Args:
            location_address: The address of the location to add
            guide_name: The name of the guide to add to
            
        Returns:
            A dictionary containing the result of the operation
        """
        try:
            if not await self.check_maps_access():
                return {
                    "success": False,
                    "message": "Cannot access Maps app. Please grant access in System Settings > Privacy & Security > Automation."
                }
            
            logger.info(f"Adding location {location_address} to guide {guide_name}")

            safe_address = escape_string(location_address)
            safe_guide = escape_string(guide_name)

            script = f'''
                tell application "Maps"
                    activate

                    -- Search for the location
                    search "{safe_address}"

                    -- Wait for search to complete
                    delay 1

                    return "SUCCESS:Location found. Click the location pin, then '...' button, and select 'Add to Guide' to add to \\"" & "{safe_guide}" & "\\""
                end tell
            '''
            
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", "")
            }
        except Exception as e:
            logger.error(f"Error adding to guide: {e}")
            return {
                "success": False,
                "message": f"Error adding to guide: {str(e)}"
            }
    
    async def create_guide(self, guide_name: str) -> Dict[str, Any]:
        """
        Create a new guide with the given name
        
        Args:
            guide_name: The name for the new guide
            
        Returns:
            A dictionary containing the result of the operation
        """
        try:
            if not await self.check_maps_access():
                return {
                    "success": False,
                    "message": "Cannot access Maps app. Please grant access in System Settings > Privacy & Security > Automation."
                }
            
            logger.info(f"Creating new guide: {guide_name}")

            safe_guide = escape_string(guide_name)

            script = f'''
                tell application "Maps"
                    activate

                    -- Open guides view
                    open location "maps://?show=guides"

                    return "SUCCESS:Opened guides view. Click '+' button and select 'New Guide' to create \\"" & "{safe_guide}" & "\\""
                end tell
            '''
            
            result = await run_applescript_async(script)
            success = result.startswith("SUCCESS:")
            
            return {
                "success": success,
                "message": result.replace("SUCCESS:", "").replace("ERROR:", "")
            }
        except Exception as e:
            logger.error(f"Error creating guide: {e}")
            return {
                "success": False,
                "message": f"Error creating guide: {str(e)}"
            }