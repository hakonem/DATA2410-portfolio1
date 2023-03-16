import argparse
import sys
from socket import *
import _thread as thread


#CLIENT HANDLER FUNCTION
#manages communication between each newly created connection socket and the server
def handleClient(connectionSocket):                         
    while True:
        try:
            message = connectionSocket.recv(1024)           #receive GET request from client (max 1024 bytes), save to 'message' variable

            #GET request arrives in following format: GET <path to file> HTTP/1.1\r\nHost: <host>\r\n\r\n

            #filename = message.split()[1]                   #extract path to requested file (second element in request line), save to 'filename' variable
            #f = open(filename[1:])                          #read path from second character (ignore initial '/'), save to 'f' variable
            #outputdata = f.read()                           #read file and store contents in 'outputdata' variable
            #f.close()                                       #close file
            data = message.decode()
            connectionSocket.send(data.upper().encode())       #if file is found, HTTP header line is sent to from connection socket to client
            #connectionSocket.send(outputdata.encode() + '\r\n'.encode())    #contents of the requested file sent to the client 
            #connectionSocket.close()                                        #close connection socket once HTML file is sent
            print('thread closed')
            break                                           #prevents server socket from closing while other clients are still connected

        #EXCEPTION HANDLING
        except IOError:
            connectionSocket.send('error!'.encode())    #if the file is not found, 404 message is returned instead
            connectionSocket.close()                                            #close client socket once message sent
            print('thread closed')
            break                                           #prevents closing server socket while other clients are still connected


#MAIN FUNCTION

def main():

    #create argparse object with program description
    parser = argparse.ArgumentParser(description='Run simpleperf network performance tool')
    #arguments with help text
    parser.add_argument('-c', '--client', help='To choose client mode', action='store_true')
    parser.add_argument('-s', '--server', help='To choose server mode', action='store_true')
    parser.add_argument('-b', '--bind', help='Enter IP address', type=str, default='127.0.0.1')
    parser.add_argument('-p', '--port', help='Enter port number', type=int, default=8088)
    parser.add_argument('-f', '--format', help='Specify format for data', type=str, choices=('B', 'KB', 'MB'), default='MB')

    #run the parser
    args = parser.parse_args()

    if (not args.client and not args.server) or (args.client and args.server):
        sys.exit('you must choose a mode')
    elif args.server:
        print('server mode')
        port_range = range(1024, 65535)
        if args.port not in port_range:
            sys.exit('port number outside permitted range')
        else:
            serverSocket = socket(AF_INET, SOCK_STREAM)             #prepare a TCP (SOCK_STREAM) server socket using IPv4 (AF_INET)
            try:
                serverSocket.bind((args.bind, args.port))                       #bind server socket to local address ('' = all available addresses) and port
            #EXCEPTION HANDLING
            except:
                print('Bind failed. Error: ')                       #print error message and terminate program if socket binding fails 
                sys.exit()
        serverSocket.listen(10)                                 #listen for incoming connection requests to socket (no more than 10 at a time)
        print('A simpleperf server is listening on port',args.port)                              #print message when socket ready to receive
        while True:
            connectionSocket,addr = serverSocket.accept()       #accept connection request from client and create new connection socket with info about the client (addr)
            print('A simpleperf client with',addr,'is connected with',args.bind,':',args.port)                  #client info printed to screen server side
            thread.start_new_thread(handleClient,(connectionSocket,))       #start new thread and return its identifier
            print('new thread started')
        serverSocket.close()                                    #close server socket
        sys.exit()                                              #terminate the program after sending the corresponding data

    else:
        print('client mode')
        client_socket = socket(AF_INET, SOCK_STREAM)        #prepare a TCP (SOCK_STREAM) client socket using IPv4 (AF_INET)
        client_socket.connect((args.bind,args.port))          #connect client socket to specified server ip/port and initiate three-way handshake

        #print('Enter the IP address, port, and path to requested file, separated by spaces')          #prompt user for input in valid format

        while True:
            test = 'this is a sample line to test for data transfer'                    #read user input (host port filename) and save in 'input' variable

            #input values need to be split up and inserted into a string to create valid GET request in format: GET <path to file> HTTP/1.1\r\nHost: <host>\r\n\r\n
            #request = 'GET /' + input.split()[2] + ' HTTP/1.1\r\nHost: ' + input.split()[0] + ':' + input.split()[1] + '\r\n\r\n'
            client_socket.send(test.encode())            #send request to server
            print(client_socket.recv(1024).decode())        #receive response (max 1024 bytes) from server (header + file contents)
            break
        client_socket.close()                               #close client socket once GET response and file content is received    


    

    #print('data given in',args.format,'format')

                
if __name__ == '__main__':
    main()                                                  #execution of module begins with main()