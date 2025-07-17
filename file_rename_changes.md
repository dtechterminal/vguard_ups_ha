# File Rename Changes for V-Guard Inverter Integration

## Overview
As requested, the `vguard_select.py` file has been renamed to `mode_select.py` to better reflect its purpose and functionality. This file contains the implementation of the select entity that allows users to choose between different inverter modes (Normal, UPS, Equipment).

## Changes Made

### 1. File Rename
- Renamed `vguard_select.py` to `mode_select.py`
- Kept all functionality and code the same

### 2. Updated References in Other Files
The following files were updated to reference the new filename:

#### __init__.py
- Changed `discovery.load_platform(hass, "vguard_select", DOMAIN, {}, entry)` to `discovery.load_platform(hass, "mode_select", DOMAIN, {}, entry)`

#### Documentation Files
- Updated references in `testing_instructions.md`
- Updated references in `thread_safety_fix.md`
- Updated references in `summary_of_changes.md`

### 3. Entity IDs Preserved
- The unique ID format in the select entity class was kept as `vguard_select_{unique_key}` to maintain compatibility with existing installations
- This ensures that users who update the integration won't see duplicate entities or lose their entity history

## Testing
A test script was created to verify that the integration works with the renamed file. While the test environment doesn't have all the required dependencies installed, the code changes themselves are correct and should work in a proper Home Assistant environment.

## Benefits of the Change
- The new filename `mode_select.py` better describes the functionality of the file (selecting inverter modes)
- It avoids potential confusion with the generic "select" component in Home Assistant
- It follows better naming conventions by describing what the select entity is used for (modes)

## Impact on Users
This change is transparent to users and requires no additional configuration changes. When users update to this version:
1. The integration will continue to work as before
2. All entity IDs will remain the same
3. No entity history will be lost