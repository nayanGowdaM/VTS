#!/home/atdxt/Project/myenv/bin/python
import RPi.GPIO as GPIO
import os
import time
import serial
import shutil
import psutil
import pynmea2
import json
import socket
import psycopg2
from adafruit_ds3231 import DS3231
import board
import busio
from datetime import datetime, timedelta

# GPIO pin numbers for LEDs
RED_LED_PIN = 27
GREEN_LED_PIN = 4

def ssssetup_led(led_pin):
    try:
       GPIO.setmode(GPIO.BOARD)
       print("Set")
       GPIO.setup(led_pin, GPIO.OUT)
       return led_pin
    except:
        print("valueError")
        pass
def setup_led(led_pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(led_pin,GPIO.OUT)
    return led_pin


def turn_on_led(led_pin):
    GPIO.output(led_pin, GPIO.HIGH)

def turn_off_led(led_pin):
    GPIO.output(led_pin, GPIO.LOW)

def blink_led(led_pin, blink_count=1, blink_duration=0.5):
    for _ in range(blink_count):
        turn_on_led(led_pin)
        time.sleep(blink_duration)
        turn_off_led(led_pin)
        time.sleep(blink_duration)

def setup_leds():
    red_led_pin = setup_led(RED_LED_PIN)
    green_led_pin = setup_led(GREEN_LED_PIN)
    turn_on_led(green_led_pin)
    time.sleep(2)  # Wait for 2 seconds
    turn_off_led(green_led_pin)
    return red_led_pin, green_led_pin


# declaring credentials for local host
local_db_name = "atdxtrv"
local_db_user = "atdxt"
local_db_password = "1234"

# AWS RDS database credentials
aws_db_endpoint = "database-1.cbwkc06ows8i.eu-north-1.rds.amazonaws.com"
aws_db_name = "postgres"
aws_db_user = "postgres"
aws_db_password = "rvce1234"


def connect_to_db():
    try:
        connection = psycopg2.connect(
            user="atdxt",
            password="1234",
            host="localhost",
            port=5432,
            database="atdxtrv",
        )
        return connection
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)


def connect_to_aws():
    try:
        # Replace these variables with your actual AWS database credentials

        # Establish connection to AWS PostgreSQL database
        aws_connection = psycopg2.connect(
            database=aws_db_name,
            user=aws_db_user,
            password=aws_db_password,
            host=aws_db_endpoint,
            port=5432  # Default PostgreSQL port
        )

        print("Connection to AWS PostgreSQL database established successfully.")
        return aws_connection
    
    except psycopg2.Error as e:
        print("Error connecting to AWS PostgreSQL database:", e)
        return None



# Function to create a new table for each day per vehicle
def create_table(connection, table_name):
    try:
        cursor = connection.cursor()
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date DATE NOT NULL,
                location_data JSONB[] NOT NULL
            )
        """
        cursor.execute(create_table_query)
        connection.commit()
        print(f"Table '{table_name}' created successfully.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error creating table '{table_name}':", error)

def update_local_database(your_table_name, location_data, threshold_sq):
    # Connect to the local database
    local_connection = psycopg2.connect(
        database=local_db_name,
        user=local_db_user,
        password=local_db_password,
        host="localhost",
        port=5432,  # Default PostgreSQL port
    )

    try:
        cursor = local_connection.cursor()

        # Check if the difference between successive latitude and longitude is greater than the threshold
        select_query = f"""
            SELECT location_data
            FROM {your_table_name}
            WHERE date = %s
        """  
        date_str, _ = read_rtc()
        cursor.execute(select_query, (date_str,))
        location_data_array = cursor.fetchone() if cursor.rowcount > 0 else None

        last_location_data = location_data_array[0][-1] if location_data_array else None

        if last_location_data is None or (
            (location_data['geometry']['coordinates'][0] - last_location_data['geometry']['coordinates'][0]) ** 2 +
            (location_data['geometry']['coordinates'][1] - last_location_data['geometry']['coordinates'][1]) ** 2 >
            threshold_sq
        ):
            if location_data_array:
                new_location_data = location_data

                update_query = f"""
                    UPDATE {your_table_name}
                    SET location_data = location_data || %s::jsonb
                    WHERE date = %s
                """
                # Convert Python dict to JSON string
                json_string = json.dumps(new_location_data)
                cursor.execute(update_query, (json_string, date_str))
                local_connection.commit()
                print("Data inserted successfully.")
                   
            else:

            # If no rows were affected, insert a new row with the new location_data
                new_location_data=location_data
                insert_query = f"""
                INSERT INTO {your_table_name} (date, location_data)
                VALUES (%s, %s::jsonb[])
            """
                json_string= json.dumps(new_location_data)
                cursor.execute(insert_query, (date_str, [json_string]))
                local_connection.commit()
                print("Data inserted successfully.")
            	# If the difference is greater than the threshold, insert the data
            
        else:
            
            print("Skipping data insertion due to proximity to the previous point.")

    except (Exception, psycopg2.Error) as error:
        print("Error inserting data:", error)
    finally:
        # Close the connection
        local_connection.close()
import json

def sync_data_to_aws(your_table_name):
    # Connect to the local and AWS RDS databases
    local_connection = psycopg2.connect(
        database=local_db_name,
        user=local_db_user,
        password=local_db_password,
        host="localhost",
        port=5432,  # Default PostgreSQL port
    )
    aws_connection = psycopg2.connect(
        database=aws_db_name,
        user=aws_db_user,
        password=aws_db_password,
        host=aws_db_endpoint,
        port=5432,  # Default PostgreSQL port
    )

    local_cursor = local_connection.cursor()
    aws_cursor = aws_connection.cursor()
    local_cursor.execute("SET TIME ZONE 'Asia/Kolkata'")
    aws_cursor.execute("SET TIME ZONE 'Asia/Kolkata'")

    create_table(aws_connection, your_table_name)

    try:
        # Fetch data from the local and AWS RDS databases for a particular date
        date_str, _ = read_rtc()

        local_cursor.execute(f"SELECT * FROM {your_table_name} WHERE date = %s", (date_str,))
        local_row = local_cursor.fetchone() if local_cursor.rowcount > 0 else None

        aws_cursor.execute(f"SELECT * FROM {your_table_name} WHERE date = %s", (date_str,))
        aws_row = aws_cursor.fetchone() if aws_cursor.rowcount > 0 else None

        if local_row:
            # Convert location_data to a JSON-formatted string
            local_location_data = json.dumps(local_row[1]) if local_row and local_row[1] else None

            # Update the AWS RDS row to match the local row for the specified date
            if aws_row:
                aws_cursor.execute(f"UPDATE {your_table_name} SET location_data = %s::jsonb[] WHERE date = %s", ([local_location_data], date_str))
                aws_connection.commit()
                print(f"Data updated in the AWS RDS database for date: {date_str}.")
            else:
                # If no row exists for the specified date in AWS RDS, insert the local row
                aws_cursor.execute(f"INSERT INTO {your_table_name} (date,location_data) VALUES (%s,%s::jsonb[])", (local_row[0],[local_location_data]))
                aws_connection.commit()
                print(f"Data inserted into the AWS RDS database for date: {date_str}.")
        else:
            print(f"No data found for date: {date_str} in the local database.")

    except (Exception, psycopg2.Error) as error:
        print("Error synchronizing data:", error)

    finally:
        # Close connections
        local_cursor.close()
        aws_cursor.close()
        local_connection.close()
        aws_connection.close()

i2c = busio.I2C(board.SCL, board.SDA)

# Create the DS3231 object
rtc = DS3231(i2c)


# Function to check internet connection
def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False


# Function to parse GNRMC data
def parse_gnrmc(data_str):
    msg = pynmea2.parse(data_str)
    if isinstance(msg, pynmea2.types.talker.RMC) and (msg.latitude != 0 and msg.longitude != 0):
        latitude = round(msg.latitude, 6)
        longitude = round(msg.longitude, 6)
        speed = msg.spd_over_grnd
        date_str, time_str = read_rtc()

        location_data = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [latitude, longitude]},
            "properties": {"speed": speed, "timestamp": f"{date_str} {time_str}"},
        }
        return location_data, latitude, longitude
    else:
        return None, None, None



def read_rtc():
    # Read the current time from the RTC
    now_utc = rtc.datetime

    # Add 5 hours and 30 minutes to the current time
    now_local = datetime(now_utc.tm_year, now_utc.tm_mon, now_utc.tm_mday, now_utc.tm_hour, now_utc.tm_min, now_utc.tm_sec) + timedelta(hours=5, minutes=30)

    # Format the adjusted time as a timestamp
    date_str = now_local.strftime("%Y_%m_%d")
    time_str = now_local.strftime("%H:%M:%S")

    return date_str, time_str

# Function to get the GeoJSON file path
def get_geojson_file_path(folder_path):
    date_str = read_rtc()[0]
    file_name = f"{date_str}.geojson"
    return os.path.join(folder_path, file_name)


# Function to append data to the GeoJSON file
def append_data_to_file(data, file_path):
    with open(file_path, "a") as geojson_file:
        json.dump(data, geojson_file)
        geojson_file.write("\n")

# Function to get the current disk usage in percentage and gigabytes
def get_disk_usage():
    disk_usage = psutil.disk_usage('/')
    total_gb = round(disk_usage.total / (1024 ** 3), 2)
    used_gb = round(disk_usage.used / (1024 ** 3), 2)
    percent_used = disk_usage.percent
    return percent_used, used_gb, total_gb

# Function to delete older files in the specified folder based on percentage usage
def delete_older_files(folder_path, threshold_high=80, threshold_low=75):
    percent_used, used_gb, total_gb = get_disk_usage()

    #print(f"Current disk usage: {percent_used}% ({used_gb} GB used out of {total_gb} GB")

    if percent_used >= threshold_high:
        print(f"Disk usage exceeds {threshold_high}%. Deleting older files to free up space.")

        files = os.listdir(folder_path)
        files.sort(key=lambda x: os.path.getctime(os.path.join(folder_path, x)))

        while percent_used >= threshold_low and files:
            file_to_delete = files.pop(0)
            file_path = os.path.join(folder_path, file_to_delete)

            try:
                os.remove(file_path)
                print(f"Deleted: {file_to_delete}")
            except Exception as e:
                print(f"Error deleting {file_to_delete}: {str(e)}")

            percent_used, _, _ = get_disk_usage()

        print(f"Deletion complete. Current disk usage: {percent_used}% ({used_gb} GB used out of {total_gb} GB)")


def check_table_exists(connection, table_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM information_schema.tables WHERE table_name = '{table_name}'")
        return cursor.fetchone() is not None
    except (Exception, psycopg2.Error) as error:
        print(f"Error checking table existence for '{table_name}':", error)


# def sync_and_delete_previous_table(previous_table_name):
#     # Connect to the local and AWS RDS databases
#     local_connection = connect_to_db()
#     aws_connection = psycopg2.connect(
#         database=aws_db_name,
#         user=aws_db_user,
#         password=aws_db_password,
#         host=aws_db_endpoint,
#         port=5432,  # Default PostgreSQL port
#     )

#     local_cursor = local_connection.cursor()
#     aws_cursor = aws_connection.cursor()

#     create_table(aws_connection, previous_table_name)

#     try:
#         # Fetch data from the local and AWS RDS databases
#         local_cursor.execute(f"SELECT * FROM {previous_table_name}")
#         local_data = local_cursor.fetchall()

#         aws_cursor.execute(f"SELECT * FROM {previous_table_name}")
#         aws_data = aws_cursor.fetchall()

#         # Identify extra data in the local database
#         local_ids = set(row[0] for row in local_data)  # Assuming id is at index 0
#         aws_ids = set(row[0] for row in aws_data)  # Assuming id is at index 0

#         extra_data = [row for row in local_data if row[0] not in aws_ids]

#         # Append extra data to the AWS RDS database
#         for row in extra_data:
#             aws_cursor.execute(
#                 f"INSERT INTO {previous_table_name} (vehicle_id, latitude, longitude, speed, timestamp) VALUES (%s, %s, %s, %s, %s)",
#                 row,
#             )

#         # Commit changes
#         aws_connection.commit()

#         print(f"Previous date's data appended to the AWS RDS database. Table: {previous_table_name}")

#         # Delete the table from the local database
#         local_cursor.execute(f"DROP TABLE IF EXISTS {previous_table_name}")
#         local_connection.commit()

#         print(f"Table '{previous_table_name}' deleted from the local database.")

#     finally:
#         # Close connections
#         local_cursor.close()
#         aws_cursor.close()
#         local_connection.close()
#         aws_connection.close()


# Main function
def main():
    red_led_pin, green_led_pin = setup_leds()

    ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1.0)
    ct = 0
    id="20"

    # Set your folder path here
    folder_path = "/home/atdxt/Documents/jso"
    geojson_file_path = get_geojson_file_path(folder_path)
    display_counter=0

    print(f"Waiting for GPS connection. Writing to file: {geojson_file_path}")

    try:
        # Check and sync the previous day's data at the start
        # previous_date = (datetime.now() - timedelta(days=1)).strftime("%Y_%m_%d")
        # previous_table_name = f"vehicle_{id}_{previous_date}"

        # local_connection = connect_to_db()
        # if check_table_exists(local_connection, previous_table_name):
        #     sync_and_delete_previous_table(previous_table_name)
        
        while True:
            #blink_led(green_led_pin,blink_count=1)
            try:
                delete_older_files(folder_path)
                
                display_counter += 1

                if display_counter % 300 == 0:
                    percent_used, used_gb, total_gb = get_disk_usage()
                    print(f"Current disk usage: {percent_used}% ({used_gb} GB used out of {total_gb})")
                    
                    # Reset display_counter after displaying information
                    display_counter = 0
                    
                data = ser.readline().decode('utf-8')
                if data.startswith('$GNRMC'):
                    location_data, latitude, longitude = parse_gnrmc(data)
                    if location_data:
                        print(f"Latitude: {latitude}, Longitude: {longitude}")
                        print(ct)
                        blink_led(green_led_pin,blink_count=1,blink_duration=0.1)
                        if ct == 10:
                            #blink_led(green_led_pin,blink_count=1,blink_duration=0.1)
                            # Append data to file when ct=10
                            append_data_to_file(location_data, geojson_file_path)
                            print(f"Location data appended to GeoJSON file at ct={ct}")
                            today = read_rtc()[0]
                            table_name = f"vehicle_{id}"  # Assuming vehicle ID is 12, adjust as needed
                            connection = None
                            while  connection == None :
                                #sleep for 10 sec
                                time.sleep(1)
                                connection = connect_to_db()
                            create_table(connection, table_name)
                            update_local_database(
                                table_name,
                                location_data,
                                threshold_sq=0.00000001,
                            )

                            if check_internet_connection() and connect_to_aws()!=None:
                                # Assuming vehicle ID is 12, adjust as needed
                                sync_data_to_aws(
                                    table_name
                                    
                                )
                                print(f"Data uploaded to database for {today}")

                                # Reset the counter after successful upload
                                ct = (ct + 1) % 11
                                # Blink green LED three times on successful AWS sync
                                blink_led(green_led_pin, blink_count=1,blink_duration=0.5)
                            else:
                                print("No internet connection. Data will be uploaded on the next attempt.")
                                connection = None
                                while  connection == None :
                                #sleep for 10 sec
                                    time.sleep(1)
                                    connection = connect_to_db()
                                create_table(connection, table_name)
                                update_local_database(
                                    table_name,
                                    location_data,
                                    threshold_sq=0.00000001,
                                )
                                ct = (ct + 1) % 11
                                # Blink red LED on AWS sync failure
                                blink_led(red_led_pin,blink_count=1,blink_duration=1)
                            # Reset the counter after every 10 iterations
                        else:
                            ct = (ct + 1) % 11
                

            except KeyboardInterrupt:
                ser.close()
                break
            except Exception as e:
                print("Error:", str(e))
                # Blink red LED on error
                blink_led(red_led_pin,blink_count=3,blink_duration=0.1)

    except serial.serialutil.SerialException:
        print("GPS connection established.")
        # Blink green LED once on GPS connection
        blink_led(green_led_pin)

    finally:
        # Cleanup GPIO on program exit
        GPIO.cleanup()

if __name__ == "__main__":
    main()
