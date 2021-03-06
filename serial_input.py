import serial, os, sys, signal, json, time

ENV                = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
DATA_PIPE          = ENV["DATA_PIPE"]
EVENT_PIPE         = ENV["EVENT_PIPE"]
BAUD               = ENV["SERIAL_BAUD_RATE"]
SERIAL             = ENV["SERIAL_ADDRESS_RPI"]
# SERIAL             = ENV["SERIAL_ADDRESS_MAC"]
PID                = ENV["PID_FILE"]
SAMPLES_PER_PACKET = ENV["STEP_SAMPLES_PER_PACKET"]

if not os.path.exists(DATA_PIPE):
	os.mkfifo(DATA_PIPE)
# Write my pid
fpid = open('./serial_pid', 'w')
fpid.write(str(os.getpid()))
fpid.close()

pipe_out = os.open(DATA_PIPE, os.O_WRONLY)
fpid     = open(PID, 'r')
pid      = fpid.read()
ser      = serial.Serial(SERIAL, BAUD, timeout=1)
count    = 0
data     = []

def signal_handler(signum, frame):
	print("Serial input terminated old connection")
	sys.exit(1)

signal.signal(signal.SIGUSR1, signal_handler)
while True:
	try:
		datum = ser.readline()
		if len(datum.split(',')) != 7:
			pass
		else:
			data.append(datum)
			count += 1
		if len(data) > 0 and count % SAMPLES_PER_PACKET == 0:
			packet = ''.join(data)
			os.write(pipe_out, packet)
			os.kill(int(pid), signal.SIGUSR1) # Raise SIGUSR1 signal
			data = []
	except serial.SerialException as e:
		print e
		print("Reopening serial port...")
		while True:
			try:
				ser = serial.Serial(SERIAL, BAUD, timeout=10)
				break
			except Exception as e:
				time.sleep(5)
				pass
	except Exception as e:
		print("Terminated serial connection")
		sys.exit(1)
