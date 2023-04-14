# DATA2410-portfolio1
Instructions:
1) To run simpleperf in server mode, use the -s flag: python3 simpleperf.py -s
* Optional arguments available in server mode:
	* -b to specify a server IP address (default: 127.0.0.1)
	* -p to specify a server port (default: 8088)
	* -f to change the format of results summary to MB, KB or B (default: MB)
3) To run simpleperf in client mode, use the -c flag: python3 simpleperf.py -c
* Optional arguments available in client mode:
	* -I to specify a server IP address (default: 127.0.0.1)
	* -p to specify a server port (default: 8088)
	* -f to change the format of results summary to MB, KB or B (default: MB)
	* -t to set the duration of data transfer in seconds (default: 25)
	* -i to print statistics per z seconds
	* -n to specify a fixed number of bytes to send as MB, KB or B (NB: cannot use this flag in conjunction with -t!)
	* -P to specify number of parallel connections to open (default: 1, max: 5)
