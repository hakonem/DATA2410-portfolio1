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


def show_results(bytes, sec):

    if args.format == 'MB':
        X = bytes/1e6
        Y = X/sec*8
    elif args.format == 'KB':
        X = bytes/1e3
        Y = X/sec*8e-3
    else:
        X = bytes
        Y = bytes*8e-6

    results = [
        ['ID', 'Interval', 'Received', 'Rate'],
        [f'{args.bind}:{str(args.port)}', '0.0 - ' + "{:.1f}".format(sec), f'{X} {args.format}', "{:.2f}".format(Y) + ' Mbps']
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

    if (not args.client and not args.server) or (args.client and args.server):
        sys.exit('Error: you must run either in server or client mode')
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
            print_msg(f'A simpleperf client with {addr} is connected with {args.bind}:{args.port}')                  #client info printed to screen server side
            data = bytearray()
            packet = connectionSocket.recv(1024)
            while connectionSocket:
                data.extend(packet)
                packet = connectionSocket.recv(1024)
                
                if b'BYE' in packet:
                    print(f'client finished: number of bytes recd: {len(data)}')
                    connectionSocket.send('ACK: BYE'.encode())
                    break
    
            show_results(len(data), args.time) 
            break
        connectionSocket.close()              
            #thread.start_new_thread(handleClient,(connectionSocket,))       #start new thread and return its identifier
            #print('new thread started')
        serverSocket.close()                                    #close server socket
        sys.exit()                                              #terminate the program after sending the corresponding data

    else:
        clientSocket = socket(AF_INET, SOCK_STREAM)        #prepare a TCP (SOCK_STREAM) client socket using IPv4 (AF_INET)
        clientSocket.connect((args.bind,args.port))          #connect client socket to specified server ip/port and initiate three-way handshake
        print_msg(f'A simpleperf client Client connecting to server {args.bind}, port {args.port}')                  #client info printed to screen server side        
             
        while True:
            chunk = '0'*1000
            packets_sent = 0
            start_time = time.time()
            duration = start_time + args.time
            
            while time.time() < duration:
                clientSocket.send(chunk.encode())
                packets_sent+=1
            print(f'finished - number of packets sent: {packets_sent}')
            clientSocket.send('BYE'.encode())
            print(clientSocket.recv(64).decode()) 
            break
        clientSocket.close()                               #close client socket 
        sys.exit('closing program')

                
if __name__ == '__main__':
    main()                                                  #execution of module begins with main()