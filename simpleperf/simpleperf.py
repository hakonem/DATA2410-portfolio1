"""
SIMPLEPERF: A simple network throughput measurement tool.
The tool must run in server and client modes to allow data packets to be sent from client to server.
The tool tracks the amount of data sent/received and calculates the rate of transmission from client/to server.
The results are then printed in a table on each side.
A number of optional arguments are available in each mode to customize the output.
"""

#Import libraries required for the program to work
import argparse
import sys
import ipaddress
from socket import *
import time 
import re
import _thread as thread
import threading


#Create argparse object with program description
parser = argparse.ArgumentParser(description='Run simpleperf network performance tool')
#Create optional arguments and assign flags. Help text describes each argument. Required input types are set, and default values set where necessary.
parser.add_argument('-s', '--server', help='Runs tool in server mode', action='store_true')
parser.add_argument('-b', '--bind', help='Takes the server IP address in decimal notation format', type=str, default='127.0.0.1')
parser.add_argument('-p', '--port', help='Takes the server port number', type=int, default=8088)
parser.add_argument('-f', '--format', help='Specifies which format to display results in', type=str, choices=('B', 'KB', 'MB'), default='MB')
parser.add_argument('-c', '--client', help='Runs tool in client mode', action='store_true')
parser.add_argument('-I', '--serverip', help='Takes the server IP address in decimal notation format, value must match -b', type=str, default='127.0.0.1')
parser.add_argument('-t', '--time', help='Total duration in seconds for which data should be generated and sent', type=int, default=25)
parser.add_argument('-i', '--interval', help='Prints statistics per <value> seconds', type=int)
parser.add_argument('-P', '--parallel', help='Specifies number of parallel connections to open', type=int, default=1)  
parser.add_argument('-n', '--num', help='Specifies fixed number of bytes to transfer, cannot be used in conjunction with -t', type=str) 

#Run the parser
args = parser.parse_args()


#FUNCTION: Check if server port is in the correct range
#ARGUMENTS: 
#portNr: port number of the server
#If the if statement fails, an error message prints to screen server side and the program is exited so the user can try again.
def check_port(portNr):
    port_range = range(1024, 65535)
    if portNr not in port_range:
        print('Error: port number must be in range 1024-65535')   
        sys.exit() 


#FUNCTION: Check if server IP address is valid and in dotted decimal notation
#ARGUMENTS: 
#ip_string: IP address of the server
#IPv4Address() returns an IPv4 address object if ip_string is a valid IPv4 address (i.e. in dotted decimal notation).
#If the try block fails, a ValueError is raised and an error message prints to screen server side. The program is exited so the user can try again.
def validate_ip(ip_string):
    try:
        ip = ipaddress.IPv4Address(ip_string)
    except ValueError:
        print('Error:',ip_string,'is not a valid IPv4 address')
        sys.exit()


#FUNCTION: Prints message to screen between two dashed lines 
#ARGUMENTS:
#msg: Message to be enclosed
#The function prints a row equal in length to the length of the message, then prints the message, then prints another dashed line of equal length.
def print_msg(msg):
    print('-'*len(msg))
    print(msg)
    print('-'*len(msg))


#FUNCTION: Generates an empty table with the correct headings (client and server tables have different headings)
#ARGUMENTS: None
#The function checks which mode it is being called from and returns an empty table with just the appropriate headings in the first row.
#Data rows are appended in a separate function. The table is only printed when a call is explicitly made, after all data rows are added.
def generate_table():
    if args.server:
        return [
            ['ID', 'Interval', 'Received', 'Rate']
        ]

    else:
        return [
            ['ID', 'Interval', 'Transfer', 'Bandwidth']
        ]
    

#FUNCTION: Generates a row of data based on values provided by the program after a successful transmission
#ARGUMENTS:
#bytes: Number of bytes sent/received (depends on mode)
#duration: In client mode, this will be the -t value. In server mode, this is the difference in the actual stop/start times recorded by the server.
#ip: In client mode: server IP address. In server mode: client IP address
#port: In client mode: server port. In server mode: client's remote port
#start: Recorded start time
#stop: Recoded stop time
#table: The empty table which has been created above and which the data row should be appended to
#The function first converts the number of bytes into the format specified by the user with -f flag (X). The rate is then calculated by dividing the 
#number of bytes by duration and converting into Mb (Y). These calculated values, as well as the other args passed into the function, are then used to
#populate the data row. If the -i flag has been activated in client mode, this row is returned by itself, so that a new row can be printed to screen 
#after each interval; otherwise the row is appended to the table so the table can be printed in its entirety.
def generate_row(bytes, duration, ip, port, start, stop, table):
    if args.format == 'MB':
        X = bytes/1e6
    elif args.format == 'KB':
        X = bytes/1e3
    else:
        X = bytes
    
    Y = (bytes/duration)*8e-6

    if args.interval:
        return [f'{ip}:{port}', f'{start:.1f} - {stop:.1f}', f'{round(X)} {args.format}', f'{Y:.2f} Mbps']
    else:
        table.append(
            [f'{ip}:{port}', f'{start:.1f} - {stop:.1f}', f'{round(X)} {args.format}', f'{Y:.2f} Mbps']
        )


#FUNCTION: Prints a new row to screen (only used in conjunction with -i)
#ARGUMENTS:
#row: The row that has been generated above
#Prints the row to screen with the following formatting: each column is right-aligned with width 20
def display_row(row):
    print("{: >20} {: >20} {: >20} {: >20}".format(*row))


#FUNCTION: Prints a complete table to screen 
#ARGUMENTS:
#table: The empty table that was generated above and any rows that have been appended to it
#Prints the table to screen with the following formatting: for each row, each column is right-aligned with width 20
def display_results(table):
    print('\n')
    for row in table:
        print("{: >20} {: >20} {: >20} {: >20}".format(*row))
 

#FUNCTION: Obtains the number of bytes to send from the -n input value
#ARGUMENTS:
#num: The string value of -n input in client mode (if given)
#-n takes a string comprising a numeric value and a format (B, KB or MB). The function splits the string on the the first non-numeric character,
#and returns the separate values in a list, saved in num_split. Then depending the format provided, the function calculates the number of bytes 
#to transmit (numeric value multiplied by the unit). This value is returned so that the program can use it to check when the desired number of
#bytes have been sent by the client.
def get_bytes_to_send(num):
    num_split = re.split('(\d+)', num)
    if num_split[2] == 'MB':
        return(int(num_split[1])*int(1e6))
    elif num_split[2] == 'KB':
        return(int(num_split[1])*int(1e3))
    else:
        return(int(num_split[1]))


#FUNCTION: Sends data from client to server
#ARGUMENTS:
#clientSocket: A client-side socket with an established connection to the server
#In all cases the function sends the duration (-t value) and start time from the client to the server. If/elif statements handle the code if
#-n or -i tags are selected; otherwise a general code takes effect for all other cases.
def send_data(clientSocket):
    #Initial conditions in all cases
    chunk = bytes(1000)                                 #Packet of 1000 bytes
    duration = args.time                                #Total time of transfer (-t value)
    formatted_duration = '{:0>3}'.format(duration)      #Format -t value as a 3-digit string (with leading zeroes if value is smaller than 3 digits)
    clientSocket.sendall(formatted_duration.encode('utf-8'))     #Send -t to server as a fixed-length message
    bytes_sent = bytearray()                            #Initialize an empty byte array to keep track of number of bytes sent
    start_time = time.time()                            #Record time that sending starts
    clientSocket.sendall(f'{start_time:7f}'.encode('utf-8').ljust(18,b'\0'))   #Send start time to server as a fixed-length message (with trailing zeroes if fewer than 7 d.p.)
    send_time = start_time + duration                   #Record time that sending should stop 
    
    #If -n selected (send given number of bytes):
    if args.num is not None:
        clientSocket.sendall('NUM'.encode('utf-8'))     #Send message to server
        #Until desired number of bytes reached:
        while len(bytes_sent) < get_bytes_to_send(args.num):
            clientSocket.sendall(chunk)                 #Send packet
            bytes_sent.extend(chunk)                    #Add packets to byte array (length of array gives number of bytes sent)
        clientSocket.sendall('BYE'.encode())            #Finished sending data - send BYE message to server
        if b'ACK' in clientSocket.recv(8):              #When ACK received from server:
            stop_time = time.time()                     #Record stop time 
        client_duration = stop_time - start_time        #Calculate client duration        
        results = generate_table()                      #Create empty table ready to hold data rows
        generate_row(len(bytes_sent), client_duration, args.serverip, args.port, 0, client_duration, results)   #Display stats with actual client duration
        display_results(results)                        #Print complete table

    #If -i selected (print stats every z seconds):
    elif args.interval is not None:
        interval = args.interval                        #Length of interval
        interval_number = int(duration/interval)        #Total time/length of interval = no. of intervals
        total_bytes_sent = 0                            #Initialize counter for total bytes sent
        total_time_taken = 0                            #Initialize counter for total time taken
        results = generate_table()                      #Create empty table ready to hold data rows
        display_results(results)                        #Print headers in empty table
        #For each interval:
        for i in range(interval_number):
            #While time is less than total send time and within interval time:
            while time.time() < start_time + interval and time.time() < send_time:                  
                clientSocket.sendall(chunk)             #Send packet
                bytes_sent.extend(chunk)                #Add packets to byte array (length of array gives number of bytes sent)
            checkpoint = time.time()                    #Record time at end of interval               
            client_duration = checkpoint - start_time   #Calculate client duration for interval
            #Create a row for the interval and save to new_row variable
            new_row = generate_row(len(bytes_sent), client_duration, args.serverip, args.port, i*interval, (i+1)*interval, results)
            display_row(new_row)                        #Print the new row in the existing table
            total_bytes_sent += len(bytes_sent)         #Update counter with number of bytes sent during interval (to calculate total)
            total_time_taken += client_duration         #Update counter with time taken during interval (to calculate total)
            start_time = time.time()                    #Reset start time for next interval
            bytes_sent = bytearray()                    #Reset byte array for next interval
        clientSocket.sendall('BYE'.encode())            #Finished sending data - send BYE message to server
        if b'ACK' in clientSocket.recv(8):              #When ACK received from server:
            stop_time = time.time()                     #Record stop time at end of total duration
        delay = stop_time - start_time                  #Time between final interval finishing and receiving ACK from server
        #Calculate totals for each column and save to total variable
        total = generate_row(total_bytes_sent, total_time_taken + delay, args.serverip, args.port, 0, duration, results) 
        print('\n' + '-'*85 + '\n')                     #Print dashed line underneath intervals
        display_row(total)                              #Print totals at bottom of table
    
    #If neither -n or -i is selected:
    else:
        #For the specified length of time (25s if -t not set explicitly):
        results = generate_table()                      #Create empty table ready to hold data rows
        while time.time() < send_time:                  
            clientSocket.sendall(chunk)                 #Send packets
            bytes_sent.extend(chunk)                    #Add packets to byte array (length of array gives number of bytes sent)
        clientSocket.sendall('BYE'.encode())            #Finished sending data - send BYE message to server
        if b'ACK' in clientSocket.recv(8):              #When ACK received from server:
            stop_time = time.time()                     #Stop timer when ACK recvd
        client_duration = stop_time - start_time        #Calculate client duration 
        generate_row(len(bytes_sent), client_duration, args.serverip, args.port, 0, duration, results)  #Display stats with -t as duration
        display_results(results)                        #Print complete table
            
    clientSocket.close()                                #Close client socket when data transmission finished


#FUNCTION: Connection handler - contains server-side code to be performed for each active connection
#ARGUMENTS:
#connectionSocket, addr: The value returned by socket.accept() in the main function, where connectionSocket is an active socket object and addr
#is the host/port bound to that socket object
#This function handles the code that is performed server side for each connection that is established
def connHandler(connectionSocket,addr):
    data = bytearray()                                  #Initialize an empty byte array to keep track of number of bytes received 
    duration_from_client = connectionSocket.recv(3)     #Server receives duration (-t) from client as fixed-length message
    duration = int(duration_from_client.decode('utf-8'))    #Convert duration string to int
    start_time_from_client = connectionSocket.recv(16)  #Server receives start time from client as fixed-length message
    start_time = float(start_time_from_client.decode('utf-8').strip('\0'))  #Convert start time string (minus any trailing zeroes) to float
    results = generate_table()                          #Create empty table ready to hold data rows

    #Only if -n is selected and client sends message:
    if b'NUM' in connectionSocket.recv(16):              
        num = True                                      #Set num to True if client sends message 
    else:
        num = False                                     #Otherwise set num to False
    
    #While the client is connected:
    while True:                                                            
        packet = connectionSocket.recv(1000)            #Receive packets of data from client
        data.extend(packet)                             #Add packets to byte array (length of array gives number of bytes received) 
        #When the server recvs BYE message from client:
        if b'BYE' in packet:                            
            stop_time = time.time()                     #Stop timer when BYE received
            server_duration = stop_time - start_time    #Calculate server duration
            connectionSocket.send('ACK: BYE'.encode())  #Server sends ACK to client
            break  
       
    #If client has selected -n (and sent message to server):
    if num:
        generate_row(len(data), server_duration, addr[0], addr[1], 0, server_duration, results)     #Display stats with actual server duration
    else:   
        generate_row(len(data), server_duration, addr[0], addr[1], 0, duration, results)            #Otherwise display -t duration
    display_results(results)                            #Print complete table
    
    
#MAIN FUNCTION
def main():
    #ERROR HANDLING IF NEITHER/BOTH MODES SELECTED
    if (not args.client and not args.server) or (args.client and args.server):
        sys.exit('Error: you must run either in server or client mode')
    #Run server first 
    elif args.server:
        check_port(args.port)                                   #Check port
        validate_ip(args.bind)                                  #Check IP address
        serverSocket = socket(AF_INET, SOCK_STREAM)             #Prepare a TCP (SOCK_STREAM) server socket using IPv4 (AF_INET)
        try:
            serverSocket.bind((args.bind, args.port))                       
        #EXCEPTION HANDLING
        except:
            print('Bind failed. Error: ')                       #Print error message and terminate program if socket binding fails 
            sys.exit()
        serverSocket.listen(5)                                  #Listen for incoming connection requests to socket (max 5)
        print_msg(f'A simpleperf server is listening on port {args.port}')    #Print message when socket ready to receive
        #While server socket is open and listening:
        while True:
            connectionSocket,addr = serverSocket.accept()       #Accept connection request from client and create new connection socket with info about the client (addr)
            print(f'A simpleperf client with {addr[0]}:{addr[1]} is connected with {args.bind}:{args.port}')     #Print confirmation of client connection
            thread.start_new_thread(connHandler,(connectionSocket,addr))    #Spawn a new thread for each client connection accepted
        connectionSocket.close()                                #Close connection socket when all client sockets are closed
        serverSocket.close()                                    #Close server socket
    #Then run client
    else:
        print_msg(f'A simpleperf client connecting to server {args.serverip}, port {args.port}')    #Print message when client request sent
        #EXCEPTION HANDLING
        if args.time <= 0:
            raise ValueError('Total duration in seconds must be greater than 0')     #Print error message if duration (-t) is less than 0
        
        conn = []                                               #List to keep track of all the newly joined connections

        #For each parallel connection specified in -P:
        for p in range(args.parallel):
            clientSocket = socket(AF_INET, SOCK_STREAM)         #Prepare a TCP (SOCK_STREAM) client socket using IPv4 (AF_INET)
            clientSocket.connect((args.serverip,args.port))     #Connect client socket to specified server IP/port and initiate three-way handshake
            print(f'Client {clientSocket.getsockname()} connected with server {args.serverip}, port {args.port}')    #Print message when client successfully connected      
            conn.append(clientSocket)                           #Add new connection to the list
    
        threads = []                                            #List to keep track of threads
        #For each active client socket:
        for clientSocket in conn:
            t = threading.Thread(target=send_data, args=(clientSocket,))    #Create a new thread to send data from the client socket
            threads.append(t)                                   #Add new thread to the list
            t.start()                                           #Start all the threads so they run concurrently
        for t in threads:
            t.join()                                            #Wait for all threads to complete before continuing
          
          
if __name__ == '__main__':
    main()                                                      #Execution of module begins with main()