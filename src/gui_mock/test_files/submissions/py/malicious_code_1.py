import os

def exfiltrate_data(file_to_read):
    try:
        with open(file_to_read, 'r') as f:
            data = f.read()
        # In a real attack, this data would be sent to a remote server.
        # For this example, we'll just print it to stdout.
        print(data)
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    # Attempt to read a sensitive file.
    exfiltrate_data('/etc/passwd')
