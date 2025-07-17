# Summary of Changes to Fix the V-Guard Inverter Integration

## Issue Description
The "Wi-Fi Signal" entity (VG011) was being initialized and updated correctly, but other entities were not being set up properly, breaking other integrations in Home Assistant.

## Root Causes Identified
1. Multiple MQTT clients causing conflicts
2. Data processing issues in the MQTT message handler
3. No state synchronization between platforms

## Changes Made

### 1. Improved MQTT Message Handling in sensor.py
- Enhanced the on_message callback to handle different data formats
- Added robust error handling and detailed logging
- Improved data unwrapping logic

### 2. Created a Shared MQTT Client
- Modified sensor.py to store its MQTT client in hass.data[DOMAIN]
- Moved the on_message callback outside the setup_platform function

### 3. Modified Other Platform Files
- Updated switch.py, number.py, and mode_select.py to use the shared client
- Added checks to ensure the sensor platform has been initialized first

## How This Fixes the Issue
Using a single shared MQTT client with improved message handling ensures all entities are properly initialized and updated, not just the Wi-Fi Signal entity.