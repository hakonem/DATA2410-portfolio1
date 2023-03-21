import argparse
import ipaddress

"""
parser = argparse.ArgumentParser(description='Run simpleperf network performance tool')
parser.add_argument('-s', '--server', help='To choose server mode', action='store_true')
parser.add_argument('-b', '--bind', help='Enter IP address', type=str, default='127.0.0.1')
   
   
args = parser.parse_args()


print(ipaddress.IPv4Address(args.bind))
"""


bind = '127.0.0.1'
port = 8088
start_time = 0
time = 3        #duration
format = 'MB'

if format == 'MB':
    x = 5000/1000
    y = x/time*8
elif format == 'KB':
    x = 5000
    y = x/time*(8e-3)
else: 
    x = 5000*1000
    y = x/time*(8e-6)


#table_data = [[ bind ],[{0:.1f}.format(time)],[f'{x} {format}'],[f'{y} Mpbs']]

table_data_1 = [
    ['a', 'b', 'c', 'dd'],
    ['aaaaaaaaa', 'bbb', 'c', 'ddddddd'],
    ['aaaaaaaaa', 'bbb', 'c', 'd'],
    ['aaa', 'bbb', 'ccccc', 'dddd']
]

server_results = [
    ['ID', 'Interval', 'Received', 'Rate'],
    [f'{bind}:{str(port)}', '0 - ' + "{:.1f}".format(time), f'{x} {format}', "{:.2f}".format(y) + ' Mbps']
]

for row in server_results:
 print("{: >20} {: >20} {: >20} {: >20}".format(*row))



