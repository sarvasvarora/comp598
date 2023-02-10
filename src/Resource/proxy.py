import socket, sys 
from threading import Thread

# Listening port and the buffer size to get client data

port = 8000 
buffer_size = 8192

def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Socket initialized")
        s.bind(('', port))
        print("Socket binded successfully")
        # Max connections of 4 TODO what should be the max_connections?
        s.listen(4)
    except Exception: 
        print("Error occured while initializing the socket")
        sys.exit(1)

    while 1:
        try:
            clntConnection, clntAddress = s.accept()
            clntData = clntConnection.recv(buffer_size).decode()
            print("Connection from: " + str(clntAddress) + " recieved " + str(clntData))

            # Starting a thread to handle the incoming request
            (Thread(target = processConnection, args = (clntConnection, clntData, clntAddress))).start()
        except: 
            s.close()
            print('Exitting proxy server')
            sys.exit(1)

def processConnection(clntConnection, clntData, clntAddress):
    try:
        if clntData == 'init':
            print("Initialize the main resource cluster.")
        # TODO Implement the proxy handlers for incoming requests
    except:
        print("Error occurred in processing the connection string")

if __name__ == '__main__':
    main()