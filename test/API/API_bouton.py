import requests
import datetime 

def action_bouton():
    url = 'http://localhost:5000/API/API_bouton'
    button_state = 'pressed'
    payload = {'button_state': button_state}
    try:    
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Response from server: {data}")
        else:
            print(f"Failed to send button state. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")    
if __name__ == '__main__':
    action_bouton() 
    
