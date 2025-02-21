import requests
import json
import csv
import logging
from datetime import datetime
import argparse

# Read configuration from config file
with open('config.json') as config_file:
    config = json.load(config_file)

API_KEY = config['api_key']
VERBOSE_LOGGING = config.get('verbose_logging', False)
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY}

# Setup logging
log_level = logging.DEBUG if VERBOSE_LOGGING else logging.INFO
logging.basicConfig(filename='device_status.log', level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

def get_organizations():
    url = 'https://api.meraki.com/api/v1/organizations'
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        logging.info(f"Successfully fetched organizations: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching organizations: {e}")
        return []

def get_device_change_history(org_id):
    url = f'https://api.meraki.com/api/v1/organizations/{org_id}/devices/availabilities/changeHistory'
    params = {
        'timespan': 2678400,  # Last 31 days in seconds
        'perPage': 1000,
        'statuses[]': ['offline', 'online']  # Correctly passing statuses as an array
    }
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        if VERBOSE_LOGGING:
            logging.debug(f"Device change history response: {json.dumps(response.json(), indent=2)}")
        logging.info(f"Successfully fetched device change history: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching device change history: {e}")
        return []

def analyze_offline_events(change_history):
    logging.info("Analyzing device offline events...")
    offline_durations = []
    device_events = {}

    for record in change_history:
        device_info = record.get('device', {})
        serial = device_info.get('serial')
        event_time = datetime.fromisoformat(record.get('ts').replace('Z', '+00:00'))
        details = record.get('details', {})
        
        old_status = next((item['value'] for item in details.get('old', []) if item['name'] == 'status'), None)
        new_status = next((item['value'] for item in details.get('new', []) if item['name'] == 'status'), None)

        if serial not in device_events:
            device_events[serial] = {
                'name': device_info.get('name'),
                'events': []
            }
        
        device_events[serial]['events'].append({
            'timestamp': event_time,
            'old_status': old_status,
            'new_status': new_status
        })

    for serial, device_data in device_events.items():
        events = device_data['events']
        events.sort(key=lambda x: x['timestamp'])
        offline_start = None
        for event in events:
            if event['old_status'] == 'online' and event['new_status'] == 'offline':
                offline_start = event['timestamp']
            elif event['old_status'] == 'offline' and event['new_status'] == 'online' and offline_start:
                offline_end = event['timestamp']
                duration = offline_end - offline_start
                total_seconds = duration.total_seconds()
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
                offline_durations.append({
                    'name': device_data['name'],
                    'serial': serial,
                    'offline_start': offline_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'offline_end': offline_end.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_of_outage': duration_str
                })
                offline_start = None
    logging.info(f"Finished analyzing device offline events.")
    return offline_durations

def save_to_csv(filename, data, fieldnames):
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logging.info(f"Successfully saved data to {filename}")
    except IOError as e:
        logging.error(f"Error saving data to CSV: {e}")

def main(org_id):
    logging.info(f"Script started for organization ID: {org_id}")

    organizations = get_organizations()
    if not organizations:
        logging.error("Failed to retrieve organizations. Exiting script.")
        return

    change_history = get_device_change_history(org_id)
    if not change_history:
        logging.error("Failed to retrieve device change history. Exiting script.")
        return

    offline_durations = analyze_offline_events(change_history)
    if offline_durations:
        save_to_csv('device_offline_durations.csv', offline_durations, ['name', 'serial', 'offline_start', 'offline_end', 'duration_of_outage'])
    else:
        logging.info("No offline durations found.")

    logging.info("Script completed successfully.")

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Retrieve device availability events.')
        args = parser.parse_args()
        
        organizations = get_organizations()
        if not organizations:
            print("Failed to retrieve organizations. Check the log file for details.")
        else:
            print("Available Organizations:")
            for idx, org in enumerate(organizations):
                print(f"{idx + 1}: {org['name']} (ID: {org['id']})")
            
            org_choice = int(input("Please enter the number of the organization you want to use: ")) - 1
            org_id = organizations[org_choice]['id']
            
            main(org_id)
            print("Process completed. Check the log file for details and the CSV files for results.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("An error occurred. Please check the log file for details.")
