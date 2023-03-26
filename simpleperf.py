import argparse
import sys
import ipaddress
from socket import *
import time 
import _thread as thread

#create argparse object with program description
parser = argparse.ArgumentParser(description='Run simpleperf network performance tool')
#arguments with help text
parser.add_argument('-s', '--server', help='Runs tool in server mode', action='store_true')
parser.add_argument('-b', '--bind', help='Enter server IP address', type=str, default='127.0.0.1')
parser.add_argument('-p', '--port', help='Enter server port number', type=int, default=8088)
parser.add_argument('-f', '--format', help='Specify which format to display results in', type=str, choices=('B', 'KB', 'MB'), default='MB')
parser.add_argument('-c', '--client', help='Runs tool in client mode', action='store_true')
parser.add_argument('-I', '--serverip', help='Enter server IP address', type=str, default='127.0.0.1')
parser.add_argument('-t', '--time', help='Enter the total duration in seconds for which data should be generated and sent', type=int, default=25)
parser.add_argument('-i', '--interval', help='Print statistics per <z> seconds', type=int)
parser.add_argument('-P', '--parallel', help='Enter number of parallel connections', type=int, default=1)
parser.add_argument('-n', '--num', help='Enter number of bytes to transfer', type=str) #NB must be B, KB or MB

#run the parser
args = parser.parse_args()

def check_port(portNr):
    port_range = range(1024, 65535)
    try: 
        if portNr not in port_range:
            raise ValueError(portNr)
    except ValueError:
        print('Error: port number must be 1024-65535')
        sys.exit()

def validate_ip(ip_string):
    try:
        ip = ipaddress.IPv4Address(ip_string)
    except ValueError:
        print('Error:',ip_string,'is not a valid IPv4 address')
        sys.exit()

def print_msg(msg):
    print('-'*len(msg))
    print(msg)
    print('-'*len(msg))

def show_results(bytes, duration, ip, port, interval):

    if args.format == 'MB':
        X = bytes/1e6
        Y = (bytes/duration)*8e-6
    elif args.format == 'KB':
        X = bytes/1e3
        Y = (bytes/duration)*8e-6
    else:
        X = bytes
        Y = (bytes/duration)*8e-6

    results = [
        ['ID', 'Interval', 'Received', 'Rate'],
        [f'{ip}:{port}', f'0.0 - {interval:.1f}', f'{round(X)} {args.format}', f'{Y:.2f} Mbps']
    ]
    for row in results:
        print('\n')
        print("{: >20} {: >20} {: >20} {: >20}".format(*row))
        


#CLIENT HANDLER FUNCTION
#manages communication between each newly created connection socket and the server
def handleClient(connectionSocket):                         
    while True:
        try:
            message = connectionSocket.recv(1024)           
            data = message.decode()
            connectionSocket.send(data.upper().encode())       
            print('thread closed')
            break                                           #prevents server socket from closing while other clients are still connected

        #EXCEPTION HANDLING
        except IOError:
            connectionSocket.send('error!'.encode())    
            connectionSocket.close()                         #close client socket once message sent
            print('thread closed')
            break                                           #prevents closing server socket while other clients are still connected


#MAIN FUNCTION
def main():

    #ERROR HANDLING IF NEITHER/BOTH MODES SELECTED
    if (not args.client and not args.server) or (args.client and args.server):
        sys.exit('Error: Simpleperf must run either in server or client mode')
    
    #SERVER MODE
    elif args.server:
        check_port(args.port)
        validate_ip(args.bind) 
        serverSocket = socket(AF_INET, SOCK_STREAM)             #prepare a TCP (SOCK_STREAM) server socket using IPv4 (AF_INET)
        try:
            serverSocket.bind((args.bind, args.port))                       
        #EXCEPTION HANDLING
        except:
            print('Bind failed. Error: ')                       #print error message and terminate program if socket binding fails 
            sys.exit()
        serverSocket.listen(args.parallel)                                 #listen for incoming connection requests to socket (specified number)
        print_msg(f'A simpleperf server is listening on port {args.port}')                              #print message when socket ready to receive
   
        
        while True:
            connectionSocket,addr = serverSocket.accept()       #accept connection request from client and create new connection socket with info about the client (addr)
            print_msg(f'A simpleperf client with {addr[0]}:{addr[1]} is connected with {args.bind}:{args.port}')                  #client info printed to screen server side
            data = bytearray()                                      #initialise an empty byte array
            interval = int(connectionSocket.recv(64).decode('utf-8'))   #recv value in -t from client
            #print(interval)
            start_time = float(connectionSocket.recv(128).decode('utf-8'))  #recv start time from client
            print(start_time)
            #print(start_time.rstrip('\x00'))
            #packet = connectionSocket.recv(1000)
            while connectionSocket:                         #while the client is connected
                packet = connectionSocket.recv(1000)        #recv packets of data from client
                data.extend(packet)                         #add the data in the packets to byte array
                
                if b'BYE' in packet:                        #when the server recvs BYE message from client:
                    stop_time = time.time()                     #stop timer when BYE recvd
                    #print(stop_time)
                    print(f'client finished: number of bytes recd: {len(data)-3}')    #CAN DELETE AFTER: print number bytes recvd
                    server_duration = stop_time - start_time
                    connectionSocket.send('ACK: BYE'.encode())          #server sends ACK to client
                    #elapsed = float(connectionSocket.recv(64).decode())
                    #print(elapsed)
                    break         
            show_results(len(data), server_duration, addr[0], addr[1], interval) 
            break
        connectionSocket.close()              
            #thread.start_new_thread(handleClient,(connectionSocket,))       #start new thread and return its identifier
            #print('new thread started')
        serverSocket.close()                                    #close server socket
        sys.exit()                                              #terminate the program after sending the corresponding data

    #CLIENT MODE
    else:
        print_msg(f'A simpleperf client connecting to server {args.serverip}, port {args.port}') 
        if args.serverip != args.bind:
            print('IP address given must match server IP address')
            sys.exit()
        clientSocket = socket(AF_INET, SOCK_STREAM)        #prepare a TCP (SOCK_STREAM) client socket using IPv4 (AF_INET)
        clientSocket.connect((args.bind,args.port))          #connect client socket to specified server ip/port and initiate three-way handshake
        print_msg(f'Client connected with server {args.serverip}, port {args.port}')                  #client info printed to screen server side        
        interval = args.time
        clientSocket.send(str(interval).encode('utf-8'))

        while True:
            #chunk = '0'*1000                                #define a chunk of data: 1000 bytes
            #chunks_sent = 0                                 #initialise chunk counter
            chunk = bytes(1000) 
            bytes_sent = bytearray()
            start_time = time.time()                        #set timer to start now
            clientSocket.send(str(start_time).encode('utf-8'))     #send start time to server
            send_time = start_time + args.time              #send data for time specified with -t flag
            while time.time() < send_time:                  #for the specified length of time:
                clientSocket.send(chunk)           #send a chunk of data
                bytes_sent.extend(chunk)
                #chunks_sent+=1                              #increase chunk counter by 1
            print(f'finished - number of bytes sent: {len(bytes_sent)}')     #CAN DELETE AFTER: print number bytes sent
            clientSocket.send('BYE'.encode())           #finished sending data - send BYE message to server
            print(clientSocket.recv(64).decode())       #recv ACK from server
            stop_time = time.time()                     #stop timer when ACK recvd
            client_duration = stop_time - start_time
            #clientSocket.send(str(elapsed).encode())
            break
        show_results(len(bytes_sent), client_duration, args.serverip, args.port, interval) 
        clientSocket.close()                               #close client socket 
        sys.exit('closing program')

                
if __name__ == '__main__':
    main()                                                  #execution of module begins with main()