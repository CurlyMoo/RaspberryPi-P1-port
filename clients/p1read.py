#!/usr/bin/python
import sys
import os
import time
import serial
import re
import datetime
import MySQLdb as mdb
from subprocess import call

verbose=1
daemon=0

ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.EIGHTBITS
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port="/dev/ttyAMA0"

newElecticitySerial=''
oldElecticitySerial=''
newElecticityRateUsedOffPeak=0
oldElecticityRateUsedOffPeak=0
newElecticityRateUsedPeak=0
oldElecticityRateUsedPeak=0
newElecticityRateGeneratedOffPeak=0
oldElecticityRateGeneratedOffPeak=0
newElecticityRateGeneratedPeak=0
oldElecticityRateGeneratedPeak=0
newElecticityCurrentRate=0
oldElecticityCurrentRate=0
newEecticityTotalUsed=0
oldElecticityTotalUsed=0
newElecticityTotalGenerated=0
oldElecticityTotalGenerated=0
newElecticityTotalGenerated=0
oldElecticityTotalGenerated=0
newElecticitySwitchPosition=0;
oldElecticitySwitchPosition=0;
newGasSerial=''
oldGasSerial=''
newGasLogDateTime='000000000000'
oldGasLogDateTime='000000000000'
newElectricityLogDateTime='000000000000'
oldElectricityLogDateTime='000000000000'
newGasTotal=0
oldGasTotal=0

try:
	ser.open()
except:
	sys.exit ("Fout bij het openen van %s. Programma afgebroken."  % ser.name)

if daemon == 1:
	try:
		pid = os.fork();
		if pid > 0:
			exit(0)
	except OSError, e:
		exit(1)

	os.chdir("/")
	os.setsid()
	os.umask(0)

	try:
		pid = os.fork()
		if pid > 0:
			exit(0)
	except OSError, e:
		exit(1)

while(1):
	p1_teller=0
	lines=[]
	while p1_teller < 20:
		p1_line=''
		try:
			p1_raw = ser.readline()
		except:
			sys.exit ("Seriele poort %s kan niet gelezen worden. Programma afgebroken." % ser.name )
		try:
			p1_str=str(p1_raw)
			p1_line=p1_str.strip()
			# print(p1_line)
			lines.append(p1_line)
			p1_teller = p1_teller +1
		except:
			break;

	if p1_teller == 20:
		for i, line in enumerate(lines[:]):
			try:
				if ":96.1.1(" in line:
					newElecticitySerial = str(re.search("[0-9]-[0-9]:96.1.1\((.*)\)",line).group(1))
				elif ":1.8.1(" in line:
					newElecticityRateUsedPeak = float("{0:.2f}".format(float(re.search("[0-9]-[0-9]:1.8.1\([0]{1,}(.*)\*kWh\)",line).group(1))))
				elif ":1.8.2(" in line:
					newElecticityRateUsedOffPeak = float("{0:.2f}".format(float(re.search("[0-9]-[0-9]:1.8.2\([0]{1,}(.*)\*kWh\)",line).group(1))))
				elif ":2.8.1(" in line:
					newElecticityRateGeneratedPeak = float("{0:.2f}".format(float(re.search("[0-9]-[0-9]:2.8.1\([0]{1,}(.*)\*kWh\)",line).group(1))))
				elif ":2.8.2(" in line:
					newElecticityRateGeneratedOffPeak = float("{0:.2f}".format(float(re.search("[0-9]-[0-9]:2.8.2\([0]{1,}(.*)\*kWh\)",line).group(1))))
				elif ":96.14.0(" in line:
					newElecticityCurrentRate = re.search("[0-9]-[0-9]:96.14.0\([0]{1,}(.*)\)",line).group(1)
				elif ":1.7.0(" in line:
					newElecticityTotalUsed = float("{0:.2f}".format(float(re.search("[0-9]-[0-9]:1.7.0\([0]{1,}(.*)\*kW\)",line).group(1))))
				elif ":2.7.0(" in line:
					newElecticityTotalGenerated = float("{0:.2f}".format(float(re.search("[0-9]-[0-9]:2.7.0\([0]{1,}(.*)\*kW\)",line).group(1))))
				elif ":96.3.10(" in line:
					newElecticitySwitchPosition = re.search("[0-9]-[0-9]:96.3.10\((.*)\)",line).group(1)
				elif ":96.1.0(" in line:
					newGasSerial = re.search("[0-9]-[0-9]:96.1.0\((.*)\)",line).group(1)
				elif ":24.2.1(" in line:
					tmp = re.search("[0-9]-[0-9]:24.2.1\(([0-9A-Za-z]{1,})\).*",line).group(1)
					newGasLogDateTime = str(time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(tmp[:-1], '%y%m%d%H%M%S')));
					newGasTotal = float(re.search(".*\(([0-9\.]{1,}).*\)",line).group(1));
				elif ":1.0.0(" in line:
					tmp = str(re.search("[0-9]-[0-9]:1.0.0\((.*)\)", line).group(1));
					newElectricityLogDateTime = str(time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(tmp[:-1], '%y%m%d%H%M%S')));

			except Exception as e:
				if verbose == 1:
					print(e);
				break;

			try:
				file = open("/cache/queries.sql", "a")

				if(newElecticitySerial != oldElecticitySerial):
					oldElecticitySerial = newElecticitySerial;
					file.write("INSERT INTO devices (name, type_id) VALUES ('%s', (SELECT type_id FROM device_types WHERE name = \'electricity\')) ON CONFLICT (name) DO UPDATE name = '%s', type_id = (SELECT type_id FROM device_types WHERE name = \'electricity\');\n" % (newElecticitySerial, newElecticitySerial))
				if(newGasSerial != oldGasSerial):
					oldGasSerial = newGasSerial;
					file.write("INSERT INTO devices (name, type_id) VALUES ('%s', (SELECT type_id FROM device_types WHERE name = \'gas\')) ON CONFLICT (name) DO UPDATE name = '%s', type_id = (SELECT type_id FROM device_types WHERE name = \'gas\');\n" % (newGasSerial, newGasSerial))
				if(newElecticityRateUsedOffPeak != oldElecticityRateUsedOffPeak):
					oldElecticityRateUsedOffPeak = newElecticityRateUsedOffPeak
					file.write("INSERT INTO consumption (dev_id, rate_id, `usage`, `datetime`, direction) VALUES ((SELECT dev_id FROM devices WHERE name = '%s'), (SELECT rate_id FROM rate_types WHERE name = 'low'), %.2f, '%s', 0);\n" % (newElecticitySerial, newElecticityRateUsedOffPeak, newElectricityLogDateTime))
				if(newElecticityRateUsedPeak != oldElecticityRateUsedPeak):
					oldElecticityRateUsedPeak = newElecticityRateUsedPeak
					file.write("INSERT INTO consumption (dev_id, rate_id, `usage`, `datetime`, direction) VALUES ((SELECT dev_id FROM devices WHERE name = '%s'), (SELECT rate_id FROM rate_types WHERE name = 'high'), %.2f, '%s', 0);\n" % (newElecticitySerial, newElecticityRateUsedPeak, newElectricityLogDateTime));
				if(newElecticityRateGeneratedOffPeak != oldElecticityRateGeneratedOffPeak):
					oldElecticityRateGeneratedOffPeak = newElecticityRateGeneratedOffPeak
					file.write("INSERT INTO consumption (dev_id, rate_id, `usage`, `datetime`, direction) VALUES ((SELECT dev_id FROM devices WHERE name = '%s'), (SELECT rate_id FROM rate_types WHERE name = 'low'), %.2f, '%s', 1);\n" % (newElecticitySerial, newElecticityRateGeneratedOffPeak, newElectricityLogDateTime));
				if(newElecticityRateGeneratedPeak != oldElecticityRateGeneratedPeak):
					oldElecticityRateGeneratedPeak = newElecticityRateGeneratedPeak
					file.write("INSERT INTO consumption (dev_id, rate_id, `usage`, `datetime`, direction) VALUES ((SELECT dev_id FROM devices WHERE name = '%s'), (SELECT rate_id FROM rate_types WHERE name = 'high'), %.2f, '%s', 1);\n" % (newElecticitySerial, newElecticityRateGeneratedPeak, newElectricityLogDateTime))
				if(newGasTotal != oldGasTotal):
					oldGasTotal = newGasTotal
					file.write("INSERT INTO consumption (dev_id, rate_id, `usage`, `datetime`, direction) VALUES ((SELECT dev_id FROM devices WHERE name = '%s'), (SELECT rate_id FROM rate_types WHERE name = 'both'), %.3f, '%s', 0);\n" % (newGasSerial, newGasTotal, newGasLogDateTime))

				if verbose == 1:
					print "-- ENERGIEMETER --"
					print ""
					print "Serienummer:\t\t"+newElecticitySerial
					print ""
					print "- Verbruikt"
					print "Daltarief:\t\t"+str(newElecticityRateUsedOffPeak)+"kWh"
					print "Piektarief:\t\t"+str(newElecticityRateUsedPeak)+"kWh"
					print ""
					print "- Teruggeleverd"
					print "Daltarief:\t\t"+str(newElecticityRateGeneratedOffPeak)+"kWh"
					print "Piektarief:\t\t"+str(newElecticityRateGeneratedPeak)+"kWh"
					print ""
					print "Huidige tarief:\t\t"+str(newElecticityCurrentRate)
					print ""
					print "Totaal verbruikt:\t"+str(newElecticityTotalUsed)
					print "Totaal teruggeleverd:\t"+str(newElecticityTotalGenerated)
					print ""
					print "Stand schakelaar:\t"+str(newElecticitySwitchPosition)
					print ""
					print "Log datum/tijd:\t\t"+newElectricityLogDateTime
					print ""
					print "-- GASMETER --"
					print ""
					print "Serienummer:\t\t"+newGasSerial
					print "Log datum/tijd:\t\t"+newGasLogDateTime
					print "Totaal:\t\t\t"+str(newGasTotal)+"m3"

			except Exception as e:
				if verbose == 1:
					print(e);
				pass
				#print "Fout bij het openen van /cache/queries.sql"

			finally:
				file.close();

ser.close();
