import serial
import pynmea2
import json
import pyrebase
import socket
import os

# Initialize Firebase with your project credenti
config = {
  "apiKey": "AIzaSyB4BUJG2t94v1ho9m8h-kDIlxvwE5Wvo2g",
  "authDomain": "atdxt3.firebaseapp.com",
  "databaseURL": "https://atdxt3-default-rtdb.firebaseio.com",
  "projectId": "atdxt3",
  "storageBucket": "atdxt3.appspot.com",
  "messagingSenderId": "721302049985",
  "appId": "1:721302049985:web:dfd2e914f6d3a62900b040"
}


firebase = pyrebase.initialize_app(config)
db = firebase.database()
storage = firebase.storage()


import socket

def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False


def parse_gprmc(data_str):
    msg = pynmea2.parse(data_str)
    if isinstance(msg, pynmea2.types.talker.RMC) and (msg.latitude!=0 and msg.longitude!=0):
        latitude = msg.latitude
        longitude = msg.longitude
        speed = msg.spd_over_grnd
        timestamp = msg.datetime.strftime("%Y-%m-%d %H:%M:%S")

        location_data = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [latitude, longitude]
            },
            "properties": {
                "speed": speed,
                "timestamp": timestamp
            }
        }

        return location_data, latitude, longitude
    else:
        return None, None, None
    
def uploadToFirebase():
    # Upload GeoJSON file to Firebase Storage
    storage.child("data.json").put("location_data.geojson")
    print("GeoJSON file uploaded to Firebase Storage")


def download_from_firebase():
    # Download the existing file from Firebase Storage
    storage.child("data.json").download("location_data.geojson")

def append_data_to_file(data):
    # Append data to the file
    with open("location_data.geojson", "a") as geojson_file:
        json.dump(data, geojson_file)
        geojson_file.write('\n')

def upload_to_firebase():
    # Re-upload the modified file back to Firebase Storage
    storage.child("data.json").put("location_data.geojson")

                            

def main():
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1.0)
    ct=0
    print("Waiting for GPS connection...")

    try:
        while True:
            try:
                data = ser.readline().decode('utf-8')
                if data.startswith('$GPRMC'):
                    location_data, latitude, longitude = parse_gprmc(data)
                    if location_data:
                        with open("location_data.geojson", "a") as geojson_file:
                            json.dump(location_data, geojson_file)
                            geojson_file.write('\n')
                            print("Location data saved as location_data.geojson")
                            print(f"Latitude: {latitude}, Longitude: {longitude}")
                            print(ct)

                        if ct == 10:
                            if check_internet_connection():
                                download_from_firebase()  # Download the file
                                append_data_to_file(location_data)  # Append data
                                upload_to_firebase()  # Upload the modified file
                                file_path = "location_data.geojson"
                                ct = 0
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    print(f"{file_path} has been erased.")
                                else:
                                    print(f"{file_path} does not exist.")    
                            else:
                                
                                ct=(ct+1)%11
                                                           
                        else:
                            ct = (ct + 1) % 11                                  
                                
                           
                            # # Send latitude and longitude to Firebase Realtime Database
                            # data_to_update = {
                            #     'latitude': latitude,
                            #     'longitude': longitude
                            # }
                            # result = db.update(data_to_update)
                            # print(f"Data uploaded to Firebase Database: {result}")
            except KeyboardInterrupt:
                ser.close()
                break
            except Exception as e:
                print("Error:", str(e))

    except serial.serialutil.SerialException:
        print("GPS connection established.")

if __name__ == "__main__":
    main()
