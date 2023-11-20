import time
import serial
import glob

# Function to send AT commands to the GSM module
def send_command(ser, command, timeout=1):
    ser.write(command.encode() + b'\r\n')
    time.sleep(timeout)
    return ser.read(ser.in_waiting).decode()

# Function to find a suitable serial port dynamically
def find_serial_port():
    ports = glob.glob('/dev/ttyUSB*')  # Adjust the pattern based on your system
    for port in ports:
        try:
            ser = serial.Serial(port, baudrate=9600, timeout=1)
            response = send_command(ser, "AT")
            ser.close()
            if "OK" in response:
                return port
        except Exception as e:
            print(f"Error checking port {port}: {e}")
    return None

# Function to read SMS messages
def read_sms(ser):
    response = send_command(ser, "AT+CMGF=1")  # Set SMS mode to text
    print(response)

    response = send_command(ser, "AT+CMGL=\"REC UNREAD\"")  # Read unread messages
    print(response)

    messages = response.split("+CMGL: ")[1:]
    return messages

# Function to parse and reply to SMS
def parse_and_reply(ser, message):
    lines = message.split('\n')
    print("Printing Lines:", lines)
    # Ensure there are enough lines to parse
    if len(lines) >= 3:
        sender_line = lines[0].strip().split(",")
        print("Sender Lines: ", sender_line)
        if len(sender_line) >= 2:
            sender = sender_line[2].strip().strip('"')
            print(sender)
            text = lines[1].strip()
            print(text)
            character_count = len(text)

            reply = f"Character count of your message: {character_count}"

            # Reply to the sender
            send_command(ser, f'AT+CMGS="{sender}"', timeout=2)
            send_command(ser, reply + '\x1A', timeout=2)
        else:
            print("Error: Sender information not found in the message.")
    else:
        print("Error: Insufficient lines in the message to parse.")

# Main function
def main():
    try:
        while True:
            port = find_serial_port()
            if port:
                print(f"Using serial port: {port}")
                # Replace the 'COMx' placeholder with the actual serial port
                ser = serial.Serial(port, baudrate=9600, timeout=1)

                messages = read_sms(ser)

                if messages:
                    print(messages)
                    most_recent_message = messages[-1]
                    parse_and_reply(ser, most_recent_message)

                ser.close()

            time.sleep(10)  # Adjust the sleep time as needed

    except KeyboardInterrupt:
        print("Script terminated by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
