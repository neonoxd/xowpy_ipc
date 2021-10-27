#!/usr/bin/python

import logging
import socket
from dataclasses import dataclass, field
from typing import List
import sys

logger = logging.getLogger('srvlogger')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

HOST = ''
PORT = 50007
levels = ["empty", "low", "medium", "full"]


@dataclass
class Controller:
	id: str
	battery_level: str


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


mapping = {
	"DN": {"fields": [{"name": "dummy"}], "description": "dongle_initialized"},
	"PS": {"fields": [{"name": "dummy"}], "description": "pairing_started"},
	"CC": {"fields": [{"name": "controller_id"}], "description": "controller_connected"},
	"CD": {"fields": [{"name": "controller_id"}], "description": "controller_disconnected"},
	"BL": {"fields": [{"name": "dummy"}, {"name": "battery_level_id"}], "description": "battery_level"}
}

controllers = {}

debug = True if len(sys.argv) > 1 else False


def log(*args):
	if debug:
		out = "LOG$"
		argstrs = [str(a) for a in args]
		out += " ".join(argstrs)
		logger.debug(out)


def display(message):
	out = ""
	if debug:
		out += "DISPLAY$"
	out += str(message)
	logger.debug(out)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	s.bind((HOST, PORT))
	s.listen(1)
	while True:
		try:
			log("accepting connections")
			conn, addr = s.accept()
			with conn:
				log('conn by', addr)
				while True:
					data = conn.recv(1024)
					if not data: break
					log("SOCK: got data", data)
					ipcmsg = IPCMSG(data)
					if ipcmsg.type_str == "DN":
						log("dongle initialized")
						display("ON")
					if ipcmsg.type_str == "PS":
						log("pairing started")
						display("PAIRING")
					if ipcmsg.type_str == "CC":
						controllers[ipcmsg.fields["controller_id"]] = Controller(ipcmsg.fields["controller_id"], "N/A")
						log(f"controllers: {controllers}")
						display(len(controllers))
					elif ipcmsg.type_str == "CD":
						del controllers[ipcmsg.fields["controller_id"]]
						log(f"controllers: {controllers}")
						display(len(controllers))
			log("xow detached")
		except KeyboardInterrupt:
			if conn:
				log("closing conn")
				conn.close()
				exit()
