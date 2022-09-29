import getopt
import os.path
import socket
import sys


def server_program(port):
    # get the hostname
    host = socket.gethostname()

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(2)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    content = ""
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode()
        if not data:
            # if data is not received break
            print("End of transmission, exiting...")
            break
        content += str(data)
        print("from connected user: " + str(data))

    with open("transmitted.txt", "w") as f:
        f.write(content)

    conn.close()  # close the connection


def client_program(port, filename):
    host = socket.gethostname()  # as both code is running on same pc

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    if not os.path.exists(filename):
        print("Error: " + filename + " file does not exists")
        sys.exit(-1)

    content = None
    with open(filename, "r") as f:
        content = f.read()

    client_socket.send(content.encode())  # send message
    print("File transmitted, exiting...")
    client_socket.close()  # close the connection


if __name__ == "__main__":
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "p:f:cs",
                                   ["port=", "filename=", "client", "server"])
    except Exception as e:
        print("Cannot load input arguments: " + e.__str__())
        sys.exit(1)

    client = False
    server = False

    filename = None

    port = 5000

    for opt, arg in opts:
        if opt in ['-p', "--port"]:
            port = int(arg)
        elif opt in ['-c', "--client"]:
            client = True
        elif opt in ['-s', "--server"]:
            server = True
        elif opt in ['-f', "--filename"]:
            filename = arg
        elif opt in ['-h', "--help"]:
            print("Usage:")
            print("-p, --port: port of the socket")
            print("-c, --client: launch client program (send 'exit' to terminate)")
            print("-s, --server: launch server program")
            sys.exit(0)

    if client and server:
        print("Error: Cannot be client and server at once!")
        print("Use -h option to print out usage of the script")
        sys.exit(-1)

    if not client and not server:
        print("Error: Specify client or server program!")
        print("Use -h option to print out usage of the script")
        sys.exit(-1)

    if client and not filename:
        print("Error: Specify path to file to send!")
        print("Use -h option to print out usage of the script")
        sys.exit(-1)

    if server:
        server_program(port)
    if client:
        client_program(port, filename)
