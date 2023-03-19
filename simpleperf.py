import argparse
import sys
import ipaddress
from socket import *
import time 
import _thread as thread

#create argparse object with program description
parser = argparse.ArgumentParser(description='Run simpleperf network performance tool')
#arguments with help text
parser.add_argument('-s', '--server', help='To choose server mode', action='store_true')
parser.add_argument('-b', '--bind', help='Enter IP address', type=str, default='127.0.0.1')
parser.add_argument('-p', '--port', help='Enter port number', type=int, default=8088)
parser.add_argument('-f', '--format', help='Specify format for summary of results', type=str, choices=('B', 'KB', 'MB'), default='MB')
parser.add_argument('-c', '--client', help='To choose client mode', action='store_true')
parser.add_argument('-I', '--serverip', help='Enter the IP address of ther server', type=str, default='127.0.0.1')
parser.add_argument('-t', '--time', help='Enter the total duration in seconds for which data should be generated', type=int, default=25)
parser.add_argument('-i', '--interval', help='Enter interval in which to display statistics', type=int)
parser.add_argument('-P', '--parallel', help='Enter number of parallel connections', type=int, default=1)
parser.add_argument('-n', '--num', help='Enter number of bytes to transfer', type=str, choices=('B', 'KB', 'MB'))


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
            connectionSocket.close()                                            #close client socket once message sent
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
        print('-'*46)
        print('A simpleperf server is listening on port',args.port)                              #print message when socket ready to receive
        print('-'*46)
        
        while True:
            connectionSocket,addr = serverSocket.accept()       #accept connection request from client and create new connection socket with info about the client (addr)
            print('-'*80)
            print('A simpleperf client with',addr,'is connected with',args.bind,':',args.port)                  #client info printed to screen server side
            print('-'*80)
            
            while connectionSocket:
                data = ''
                packet = connectionSocket.recv(4096).decode()
                data += packet
                chunks = [data[i:i+1000] for i in range(0, len(data), 1000)]
                print(chunks)

                if 'BYE' in packet:
                    print('client finished')
                    connectionSocket.send('ACK: BYE'.encode())
                    
                    break
      
            #thread.start_new_thread(handleClient,(connectionSocket,))       #start new thread and return its identifier
            #print('new thread started')
        serverSocket.close()                                    #close server socket
        sys.exit()                                              #terminate the program after sending the corresponding data

    else:
        clientSocket = socket(AF_INET, SOCK_STREAM)        #prepare a TCP (SOCK_STREAM) client socket using IPv4 (AF_INET)
        clientSocket.connect((args.bind,args.port))          #connect client socket to specified server ip/port and initiate three-way handshake
        print('-'*70)
        print('A simpleperf client Client connecting to server',args.bind,', port',args.port)                  #client info printed to screen server side
        print('-'*70)
        
              
        while True:
            chunk = '0'*1000
        
            duration = time.time() + args.time
            
            while time.time() < duration:
                clientSocket.send(chunk.encode())
                
            print('finished')
            clientSocket.send('BYE'.encode())
            print(clientSocket.recv(64).decode()) 
            

        clientSocket.close()                               #close client socket 


                
if __name__ == '__main__':
    main()                                                  #execution of module begins with main()