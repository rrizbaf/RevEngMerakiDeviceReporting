Overview
This script fetches the device availability events from Cisco Meraki and calculates the offline duration for each device. The results are saved to a CSV file with detailed information about each offline event.

Prerequisites
Python 3.x installed on your system

requests library: Install it using pip install requests

Cisco Meraki API Key

A config file named config.json

Config File (config.json)
The config.json file should contain the following structure:

json
{
    "api_key": "your_api_key_here",
    "verbose_logging": false
}
api_key: Your Cisco Meraki API key.

verbose_logging: Set this to true if you want detailed logging, otherwise false.

Script Usage
Save the Script and Config File: Ensure the script file (devicestatusreport.py) and the config file (config.json) are in the same directory.

Run the Script: Execute the script using the following command:

bash
python3 devicestatusreport.py
Choose an Organization: The script will fetch available organizations and prompt you to choose one by entering the corresponding number.

Check the Output: Once the script completes, it will generate a CSV file named device_offline_durations.csv containing the offline duration details of each device.

Logging
The script logs key information to a file named device_status.log. The logging includes:

Success messages for fetching organizations and device change history.

Errors encountered during the execution.

Detailed debug information if verbose logging is enabled.

Example Output
The CSV file device_offline_durations.csv will have the following columns:

name: Name of the device.

serial: Serial number of the device.

offline_start: Timestamp when the device went offline.

offline_end: Timestamp when the device came back online.

duration_of_outage: The duration for which the device was offline.
