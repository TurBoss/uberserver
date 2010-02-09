import Multiplexer, Protocol, Client
import socket, thread

class Dispatcher:
	def __init__(self, root, server):
		self._root = root
		self.server = server
		self.poller = Multiplexer.BestMultiplexer()
		self.socketmap = {}
		self.workers = []
		self.protocol = Protocol.Protocol(root, self)
		# legacy vars
		self.thread = thread.get_ident()
		self.num = 0
	
	def pump(self):
		self.poller.register(self.server)
		self.poller.pump(self.callback)
	
	def callback(self, inputs, outputs, errors):
		for s in inputs:
			if s == self.server:
				try:
					conn, addr = self.server.accept()
				except socket.error, e:
					if e[0] == 24: # ulimit maxfiles, need to raise ulimit
						self._root.console_write('Maximum files reached, refused new connection.')
					else:
						raise socket.error, e
				client = Client.Client(self._root, conn, addr, self._root.session_id)
				self.addClient(client)
			else:
				try:
					data = s.recv(1024)
					if data:
						if s in self.socketmap: # for threading, just need to pass this to a worker thread... remember to fix the problem for any calls to handler, and fix msg ids (handler.thread)
							self.socketmap[s].Handle(data)
						else:
							print 'Problem, sockets are not being cleaned up properly.'
					else:
						raise socket.error, 'Connection closed.'
				except socket.error:
					self.removeSocket(s)
		
		for s in outputs:
			try:
				self.socketmap[s].FlushBuffer()
			except KeyError:
				self.removeSocket(s)
			except socket.error:
				self.removeSocket(s)

	def addClient(self, client):
		self._root.clients[self._root.session_id] = client
		self._root.session_id += 1
		client.Bind(self, self.protocol)
		if not client.static:
			self.socketmap[client.conn] = client
			self.poller.register(client.conn)
	
	def removeClient(self, client, reason='Quit', remove=True):
		if client.static: return # static clients don't disconnect
		self.removeSocket(client.conn, remove)
		self._root.console_write('Client disconnected from %s, session ID was %s'%(client.ip_address, client.session_id))
		client._protocol._remove(client, reason)
	
	def removeSocket(self, s, remove=True):
		self.poller.unregister(s)
		if s in self.socketmap:
			client = self.socketmap[s]
			del self.socketmap[s]
			if remove: client.Remove()
		try: sock.close()
		except: pass