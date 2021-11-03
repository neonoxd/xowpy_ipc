#!/usr/bin/python

import logging
import socket
from dataclasses import dataclass, field
from typing import List
import sys
import signal

logger = logging.getLogger('srvlogger')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


@dataclass
class IPCMSG:
	type_str: str
	fields: dict = field(default_factory=dict)
	data: List[str] = field(default_factory=list)

	def __init__(self, ipc_data):
		data_str_arr = ipc_data.decode().split("|")
		self.fields = {}
		self.data = data_str_arr
		self.type_str = self.data[0]
		definition = mapping[self.type_str]
		i = 1
		for fm in definition["fields"]:
			self.fields[fm['name']] = data_str_arr[i]
			i += 1

	def __str__(self):
		definition = mapping[self.type_str]
		i = 1
		out = f"MSG:{definition['description']}"
		for fm in definition["fields"]:
			out += f"\n\t{fm['name']}: [{self.data[i]}]"
			i += 1
		return out


@dataclass
class Controller:
	controller_id: str
	battery_level: str

	def __init__(self, controller_id, battery_level):
		self.controller_id = controller_id
		self.battery_level = battery_level

	def __str__(self):
		return f"{self.controller_id} - {self.battery_level}"


battery_levels = ["empty", "low", "medium", "full"]

ipc = {
	"DONGLE_ON": "DN",
	"PAIRINGSTART": "PS",
	"CONTROLLERCONN": "CC",
	"CONTROLLERDC": "CD",
	"BATTERYLVL": "BL"
}
mapping = {
	ipc["DONGLE_ON"]: {"fields": [{"name": "dummy"}], "description": "dongle_initialized"},
	ipc["PAIRINGSTART"]: {"fields": [{"name": "dummy"}], "description": "pairing_started"},
	ipc["CONTROLLERCONN"]: {"fields": [{"name": "controller_id"}], "description": "controller_connected"},
	ipc["CONTROLLERDC"]: {"fields": [{"name": "controller_id"}], "description": "controller_disconnected"},
	ipc["BATTERYLVL"]: {"fields": [{"name": "dummy"}, {"name": "battery_level_id"}], "description": "battery_level"}
}


class IPCServer:

	def __init__(self, host='', port=50007, args=[]):
		self.host = host
		self.port = port
		self.controllers = []
		self.debug = True if "-d" in args else False
		self.last_msg_type = None

	def log(self, *args):
		if self.debug:
			out = "LOG$"
			argstrs = [str(a) for a in args]
			out += " ".join(argstrs)
			logger.debug(out)

	def display(self, message, msgtype=None):
		self.last_msg_type = msgtype
		out = ""
		if self.debug:
			out += "DISPLAY$"
		out += str(message)
		logger.debug(out)

	def display_battery_status(self):
		self.display(" / ".join([str(controller) for controller in self.controllers]), 'BC')

	def handle_battery_status_check_signal(self):
		if not self.connected_controllers():
			return
		if self.last_msg_type != "BC":
			self.display_battery_status()
		else:
			self.display(self.connected_controllers())

	def connected_controllers(self):
		return len(self.controllers)

	def handle_controller_connected(self, ipc_message):
		self.controllers.append(Controller(
			ipc_message.fields["controller_id"],
			"N/A"))
		self.log(f"controllers: {self.controllers}")
		self.display(len(self.controllers))

	def handle_controller_disconnected(self, ipc_message):
		self.controllers = [i for i in self.controllers if not (i.controller_id == ipc_message.fields["controller_id"])]
		self.log(f"controllers: {self.controllers}")
		self.display(self.connected_controllers())

	def handle_got_battery_level(self, ipc_message):
		if len(self.controllers) > 0:
			self.controllers[-1:][0].battery_level = battery_levels[int(ipc_message.fields["battery_level_id"])]
		self.log(f"controllers: {self.controllers}")
		self.handle_battery_status_check_signal()

	def handle_ipc_message(self, ipc_message):
		if ipc_message.type_str == ipc["DONGLE_ON"]:
			self.log("dongle initialized")
			self.display("ON")
		elif ipc_message.type_str == ipc["PAIRINGSTART"]:
			self.log("pairing started")
			self.display("PAIRING")
		elif ipc_message.type_str == ipc["CONTROLLERCONN"]:
			self.handle_controller_connected(ipc_message)
		elif ipc_message.type_str == ipc["CONTROLLERDC"]:
			self.handle_controller_disconnected(ipc_message)
		elif ipc_message.type_str == ipc["BATTERYLVL"]:
			self.handle_got_battery_level(ipc_message)

	def loop(self):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind((self.host, self.port))
			s.listen(1)
			while True:
				conn = None
				try:
					self.log("accepting connections")
					conn, addr = s.accept()
					with conn:
						self.log('incoming connection', addr)
						while True:
							data = conn.recv(1024)
							if not data: break
							self.log("SOCK: got data", data)
							ipcmsg = IPCMSG(data)
							self.handle_ipc_message(ipcmsg)
					self.log("client disconnected")
				except KeyboardInterrupt:
					if conn:
						self.log("closing connection")
						conn.close()
					exit(0)


def onsig1(*args):
	server.log(f"got SIGUSR1 {args}")
	server.handle_battery_status_check_signal()


def onsig2(*args):
	# UNUSED
	server.log(f"got SIGUSR2 {args}")


signal.signal(signal.SIGUSR1, onsig1)
signal.signal(signal.SIGUSR2, onsig2)
server = IPCServer(args=sys.argv[1:])
server.loop()
