###
# Author: Eduard Haag
#
# Created on 11.02.2016
#
# 11.02.2016 initial alpha version with support command line
#
###

import os, sys
import socket
import time
import struct
import argparse

def htoll(x):
  return (((x) & 0xFF000000) >> 24) | (((x) & 0x00FF0000) >> 8) | (((x) & 0x0000FF00) << 8) | (((x) & 0x000000FF) << 24)

def byte(number, i):
    return (number & (0xff << (i * 8))) >> (i * 8)

def recvall(sock):
    data = ""
    part = None
    while part != "":
        part = sock.recv(4096)
        data += part
    return data

# Get sdb host version
def get_host_version():
  sock = socket.socket()
  sock.connect((sdb_host, sdb_port))
  sock.send('000chost:version')
  data = sock.recv(1024)
  print data
  if ("OKAY" in data):
    sock.close()
    return 0
  else:
    sock.close()
    print data
    return -1

# Make directory on remote device
def remote_mkdir():
  return 0

# Kill application
def app_kill():
  sock = socket.socket()
  sock.connect((sdb_host, sdb_port))
  sock.send('001dhost:transport:' + device_id)
  data = sock.recv(1024)
  print data
  if ("OKAY" in data):
    sock.send('001cshell:2 kill "' + app_id + '" ' + certificate_name)
    data = recvall(sock)
    sock.close()
    print data
    return 0
  else:
    sock.close()
    print data
    return -1

# Check application running status
def app_check_running():
  sock = socket.socket()
  sock.connect((sdb_host, sdb_port))
  sock.send('001dhost:transport:' + device_id)
  data = sock.recv(1024)
  print data
  if ("OKAY" in data):
    sock.send('001dshell:1 runcheck "' + app_id + '"');
    data = recvall(sock)
    sock.close()
    print data
    if ("is Running" in data):
      return 1
    return 0
  else:
    sock.close()
    print data
    return -1

# Application uninstall
def app_uninstall():
  sock = socket.socket()
  sock.connect((sdb_host, sdb_port))
  sock.send('001dhost:transport:' + device_id)
  data = sock.recv(1024)
  print data
  if ("OKAY" in data):
    #cmd = '0052shell:0 vd_appuninstall "' + app_id + '.' + app_name + '"; echo cmd_ret:$?;'
    cmd = '003bshell:0 vd_appuninstall "' + app_id + '.' + app_name + '"; echo cmd_ret:$?;'
    print cmd
    sock.send(cmd)
    data = recvall(sock)
    sock.close()
    print data
    return 0
  else:
    sock.close()
    print data
    return -1

# Application install
def app_install():
  sock = socket.socket()
  sock.connect((sdb_host, sdb_port))
  sock.send('001dhost:transport:' + device_id)
  data = sock.recv(1024)
  print data
  if ("OKAY" in data):
    sock.send('0056shell:0 vd_appinstall "' + app_id + '.' + app_name + '" "' + device_app_wgt_path + '"; echo cmd_ret:$?;')
    data = recvall(sock)
    sock.close()
    print data
    if ("install completed" in data):
      return 0
    else:
      return -1    
    return 0
  else:
    return -1

# Application transfer
def app_push():
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((sdb_host, sdb_port))
  sock.send('001dhost:transport:' + device_id)
  data = sock.recv(1024)
  print data
  if ("OKAY" in data):
    sock.send('0005sync:')
    data = sock.recv(1024)
    if ("OKAY" in data):

      st_mode = os.stat(local_wgt_path).st_mode
      m_time = int(os.stat(local_wgt_path).st_mtime)
      file_size = os.stat(local_wgt_path).st_size
      l = len(device_app_wgt_path) + len(str(st_mode)) + 1

      cmd =  'SEND' + chr(byte(htoll(l), 3)) + chr(byte(htoll(l), 2)) + chr(byte(htoll(l), 1)) + chr(byte(htoll(l), 0))
      cmd += device_app_wgt_path + ',' + str(st_mode)

      f = open(local_wgt_path, 'rb')
      byt = None
      bytes_sent = 0
      buf_size_max = 65536
      try:
        while(byt != ""):
          if (file_size - bytes_sent > buf_size_max):
            buf_size = buf_size_max
          else:
            buf_size = file_size - bytes_sent
          byt = f.read(buf_size)         
          cmd += 'DATA' + chr(byte(htoll(buf_size), 3)) + chr(byte(htoll(buf_size), 2)) + chr(byte(htoll(buf_size), 1)) + chr(byte(htoll(buf_size), 0)) + byt
          bytes_sent += buf_size
      finally:
        f.close()

      cmd += 'DONE'
      cmd += chr(byte(htoll(m_time), 3)) + chr(byte(htoll(m_time), 2)) + chr(byte(htoll(m_time), 1)) + chr(byte(htoll(m_time), 0))
      sock.send(cmd)
      data = sock.recv(1024)
      if ("OKAY" in data):
        sock.send("QUIT")
        sock.close()
        return 0
      else:
        sock.close()
        return -1
    else:
      sock.close()
      return -1
  else:
    sock.close()
    return -1

### main
parser = argparse.ArgumentParser(description='Samsung Tizen SmartTV application deploy.')
parser.add_argument('sdb_host', metavar='sdb_host', type=str,
                   help='sdb host ip address')
parser.add_argument('sdb_port', metavar='sdb_port', type=int,
                   help='sdb host port')
parser.add_argument('app_id', metavar='app_id', type=str,
                   help='application identifier')
parser.add_argument('app_name', metavar='app_name', type=str,
                   help='application name')
parser.add_argument('device_id', metavar='device_id', type=str,
                   help='sdb device identifier')
parser.add_argument('wgt_file', metavar='wgt_file', type=str,
                   help='application wgt file location')
parser.add_argument('certificate_name', metavar='certificate_name', type=str,
                   help='certiticate_name')

args = parser.parse_args()
if not args:
  exit(0)

sdb_host = args.sdb_host
sdb_port = args.sdb_port
app_id = args.app_id
app_name = args.app_name
device_id = args.device_id
device_app_wgt_path = '/opt/usr/apps/tmp/' + app_name + '.wgt'
certificate_name = args.certificate_name
local_wgt_path = args.wgt_file

print "Welcome to Samsung SmartTV SDB deploy system"
print "Deploy started"
print "Get host version"
if (get_host_version() == 0):
  print "Get host version success"
  print "Check application running status"
  ret = app_check_running()
  if (ret == 1):
    print "Application is running"
    print "Kill application"
    app_kill()
  elif (ret == 0):
    print "Application is not running or not installed"
  else:
    print "Application check running failed"
    exit(-1)
  print "Uninstall application"
  if (app_uninstall() == 0):
    print "Uninstall application complete"
  else:
    print "Uninstall application failed"
    exit(-1)
  print "Transfer application"
  if (app_push() == 0):
    print "Transfer application complete"
  else:
    print "Transfer application error"
    exit(-1)
  print "Install application"
  if (app_install() == 0):
    print "Install application complete"
  else:
    print "Install application failed"
    exit(-1)
  exit (0)
  print "Deploy complete"
else:
  print "Get host version failed"
  exit (-1)
