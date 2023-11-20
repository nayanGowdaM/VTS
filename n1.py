import time
import serial

# Function to send AT commands to the GSM module
def send_command(ser, command, timeout=1):
    ser.write(command.encode() + b'\r\n')
    time.sleep(timeout)
    return ser.read(ser.in_waiting).decode()

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
    print("Printing Lines:",lines)
    # Ensure there are enough lines to parse
    if len(lines) >= 3:
        sender_line = lines[0].strip().split(",")
        print("Sender Lines: ",sender_line)
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
    # Replace 'COMx' with the actual serial port where your GSM module is connected
    ser = serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=1)

    try:
        while True:
            messages = read_sms(ser)

            if messages:
                print(messages)
                most_recent_message = messages[-1]
                parse_and_reply(ser, most_recent_message)

            time.sleep(10)  # Adjust the sleep time as needed

    finally:
        ser.close()

if __name__ == "__main__":
    main()

