#!/usr/bin/python3

#Actualizado a python3 por: Clun0x

import sys
import socket
import getopt
import threading
import subprocess
import signal

#Ctrl+C
#def exit(sig, frame):
#	print("\n[!] Saliendo...\n")
#	sys.exit(1)

#signal.signal(signal.SIGINT, exit)

#Variables globales
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
	print("\t\n\nNetCat en python3\n")
	print
	print("\tUso: python3 netcat.py -t target_host -p port\n")
	print("\t[-l] --listen\t\t\t- escuchar en el [host]:[port] para conexiones entrantes")
	print("\t[-e] --execute=file_to_run\t- ejecutar un archivo luego de recibir una conexion")
	print("\t[-c] --command\t\t\t- ejecutar una shell de commandos")
	print("\t[-u] --upload=destination\t- al recibir una shell subir un archivo y escribit el path[destino]")
	print
	print("\tEjemplos: ")
	print("\n\t\tpython3 netcat.py -t 192.168.1.3 -p 5555 -l -c")
	print("\t\tpython3 netcat.py -t 192.168.1.3 -p 5555 -l -u=c:\\target.exe")
#	print("\t\tpython3 netcat.py -t 192.168.1.3 -p 5555 -l -e=\"cat /etc/passwd\"")
	print("\t\techo 'AEEAFASD' | python3 netcat.py -t 192.168.11.33 -p 123")
	sys.exit(0)

def client_sender():

	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try :
		#Conexion con el puerto y el host
		client.connect((target,port))
		print("Conexion establecida de %s:%s" % (target,port))
		#if len(buffer):
		#	client.send(buffer.encode('utf-8'))

		while True:
			#ahora esperamos la data de regreso
			recv_len = 1
			response = ""

			while recv_len:

				data = client.recv(4096).decode('utf-8')
				recv_len = len(data)
				response += data

				if recv_len < 4096:
					break

			print(response)
			#Espera para mas entradas
			buffer = str(input(""))
			buffer += "\n"

			#Enviamos
			client.send(buffer.encode('utf-8'))

	except:
		print("\n[!] No se pudo conectar")
		print("\n[!] Saliendo...\n")

		#Cortando la conexion
		client.close()

def server_loop():
	global target

	#Si el target no esta definido, escucharemos en todas las interfaces
	if not len(target):
		target = "0.0.0.0"

	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((target,port))
	print("Esperando conexiones...\n")
	server.listen(5)

	while True:
		client_socket, addr = server.accept()
		print("Conexion recibida de %s: %s" % addr)
		#Creamos un hilo para manejar nuevos clientes
		client_thread = threading.Thread(target=client_handler,args=[client_socket, ])
		client_thread.start()

def run_command(command):
	#Recortar la nueva linea
	command = command.rstrip()
	#Enviamos el comando y obtenemos la respuesta
	try:
		output = subprocess.check_output(command,stderr=subprocess.STDOUT, shell=True)
	except:
		output = "Error al ejecutar el comando.\r\n"
	#Enviamos el output al cliente
	return output

def client_handler(client_socket):
	global upload
	global execute
	global command
	#Comprobar la carga
	if len(upload_destination):
		#Leer los bytes y escribir en el destino
		file_buffer = ""
		print("esperando para escribir en %s..\n" % upload_destination)
		#Seguir leyendo los datos hasta que no haya ninguno disponible
		while True:
			file_buffer = ""

			while True:
				client_socket.send(b' Introduzca el contenido del archivo:\n')
				print("Recibiendo...")
				data = client_socket.recv(1024)
				print("La data es %s" % data)
				if b'exit' in data:
					break
				else:
					file_buffer += data.decode('utf-8')
			print("EL file_buffer es %s\n" % file_buffer)

			#Abrimos el archivo con los bytes y intentamos escribir
			try:
				file_descriptor = open(upload_destination,"wb")
				file_descriptor.write(file_buffer)
				file_descriptor.close()

				#Enviamos que el archivo se subio
				client_socket.send(b'Archivo guardado correctamente en %s\r\n' % upload_destination.encode('utf-8'))
			except:
				client_socket.send(b'Error al guardar el archivo en %s\r\n' % upload_destination.encode('utf-8'))

	 #Comprobamos la ejecution de commandos
	if len(execute):

	 	output = run_command(execute).encode('utf-8')

	 	client_socket.send(output)

	 #Entramos en otr bucle si se solicito un commando en shell
	if command:

	 	while True:
	 		#Mostrar un simple prompt
	 		client_socket.send(" \n<$: > ".encode('utf-8'))

	 		#Ahora esperamos hasta ver un salto de linea (enter key)
	 		cmd_buffer = ""
	 		while "\n" not in cmd_buffer:
	 			cmd_buffer += client_socket.recv(1024).decode('utf-8')

	 		#Enviar el output de vuelta
	 		response = bytes(run_command(cmd_buffer))

	 		client_socket.send(response)

def main():
	global listen
	global port
	global execute
	global command
	global upload_destination
	global target

	if not len(sys.argv[1:]):
		usage()

	#Leer los commandos
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",["help","listen","execute","target","port","command","upload"])
	except getopt.GetoptError as e:
		print(str(e))
		usage()

	for o,a in opts:
		if o in ("-h","--help"):
			usage()
		elif o in ("-l","--listen"):
			listen = True
		elif o in ("-e","--execute"):
			execute = a
		elif o in ("-c","--command"):
			command = True
		elif o in ("-u","--upload"):
			upload_destination = a
		elif o in ("-t","--target"):
			target = a
		elif o in ("-p","--port"):
			port = int(a)
		else:
			assert False,"Opcion invalida"
	#Vamos a escuchar, si no reibimos datos enviamos esto
	if not listen and len(target) and port > 0:

		#Si no se recibe la Standar Input enviaremos Ctrl+D para matar
		#buffer = sys.stdin.read()

		#enviar datos
		client_sender()

	#Si recibimos datos, podremos ejecutar comandos y obtener una shell con los commandos de uso
	if listen:
		server_loop()

main()
