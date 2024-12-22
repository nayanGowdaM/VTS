#!/home/atdxt/Project/myenv/bin/python
import psycopg2
import json
import requests
from datetime import datetime, timedelta
from adafruit_ds3231 import DS3231
import board
import busio
import time
import socket

# Connect to the RTC
i2c = busio.I2C(board.SCL, board.SDA)
rtc = DS3231(i2c)# declaring credentials for local host
local_db_name = "atdxtrv"
local_db_user = "atdxt"
local_db_password = "1234"

# AWS RDS database credentials
aws_db_endpoint = "database-1.cbwkc06ows8i.eu-north-1.rds.amazonaws.com"
aws_db_name = "postgres"
aws_db_user = "postgres"
aws_db_password = "rvce1234"




# Function to connect to the local database
def connect_to_local_db():
    try:
        connection = psycopg2.connect(
            database=local_db_name,
            user=local_db_user,
            password=local_db_password,
            host="localhost",
            port=5432
        )
        return connection
    except psycopg2.Error as e:
        print("Error connecting to local database:", e)
        return None

# Function to connect to the AWS RDS database
def connect_to_aws_db():
    try:
        connection = psycopg2.connect(
            database=aws_db_name,
            user=aws_db_user,
            password=aws_db_password,
            host=aws_db_endpoint,
            port=5432
        )
        return connection
    except psycopg2.Error as e:
        print("Error connecting to AWS RDS database:", e)
        return None

# Function to compare and update data in AWS database
# Function to compare and update data in AWS database
def update_aws_db(connection_local, connection_aws, table_name):
    try:
        cursor_local = connection_local.cursor()
        cursor_aws = connection_aws.cursor()

        cursor_local.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor_local.fetchone()[0]

        while count >= 3:
            print("There are", count, "or more rows in the local database.")

            cursor_local.execute(f"SELECT date, location_data FROM {table_name} ORDER BY date LIMIT 1")
            first_row = cursor_local.fetchone()

            if first_row is not None:
                date, json_dat = first_row
                json_data=json.dumps(json_dat)

                cursor_aws.execute(f"SELECT location_data FROM {table_name} WHERE date = %s", (date,))
                aws_data = cursor_aws.fetchone()

                if aws_data is not None:
                    aws_json = json.dumps(aws_data[0])
                    if len(json.loads(aws_json)) != len(json.loads(json_data)):
                        cursor_aws.execute(f"UPDATE {table_name} SET location_data = %s::jsonb[] WHERE date = %s", ([json_data], date))
                        connection_aws.commit()
                        print("Updated AWS data for date:", date)
                    else:
                        print("AWS data already up-to-date for date:", date)
                else:
                    # If there's no corresponding record in AWS, insert a new one
                    cursor_aws.execute(f"INSERT INTO {table_name} (date, location_data) VALUES (%s, %s::jsonb[])", (date, [json_data]))
                    connection_aws.commit()
                    print("Inserted new record into AWS for date:", date)
                

                cursor_local.execute(f"DELETE FROM {table_name} WHERE date = %s", (date,))
                connection_local.commit()
                print("Deleted row from local database for date:", date)

                cursor_local.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor_local.fetchone()[0]
            else:
                print("No rows found in the table.")
                break

        if count < 3:
            print("There are", count, "or fewer rows in the local database. No action required.")
    
    except psycopg2.Error as e:
        print("Error updating AWS database:", e)



# Function to read the current date from RTC
def read_rtc_date():
    now_utc = rtc.datetime
    now_local = datetime(now_utc.tm_year, now_utc.tm_mon, now_utc.tm_mday)
    return now_local

# Function to check internet connectivity
def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

# Main function
def main():
    last_execution_date = None
    id="20"
    table_name = f"vehicle_{id}"  # Change this to your table name

    while True:
        if check_internet_connection():
            current_date = read_rtc_date()

            # Check if it's a new day
            if current_date != last_execution_date:
                last_execution_date = current_date
                print("Performing database check and update for date:", current_date)

                local_connection = connect_to_local_db()
                aws_connection = connect_to_aws_db()

                if local_connection and aws_connection:
                    try:
                        # Perform operations on AWS database
                        update_aws_db(local_connection, aws_connection, table_name)
                    except Exception as e:
                        print("Error occurred while updating AWS database:", e)
                        continue
                    finally:
                        # Close connections
                        if local_connection:
                            local_connection.close()
                        if aws_connection:
                            aws_connection.close()

                    # Wait for 24 hours before checking again
                    # This ensures the script runs once a day
                    next_execution_date = read_rtc_date() + timedelta(days=1)
                    time_until_next_execution = next_execution_date - read_rtc_date()
                    time.sleep(time_until_next_execution.total_seconds())

if __name__ == "__main__":
    main()
