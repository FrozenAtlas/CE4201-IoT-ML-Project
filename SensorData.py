import time
import board
import adafruit_ccs811 #airqual
import adafruit_si7021 #temp&huma
from adafruit_seesaw.seesaw import Seesaw #soil sensor
import mysql.connector
import pytz
from datetime import datetime, timezone
from tzlocal import get_localzone
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="IOTLab"
)

mycursor = mydb.cursor()

i2c = board.I2C()  # uses board.SCL and board.SDA
ccs811 = adafruit_ccs811.CCS811(i2c)
sensor = adafruit_si7021.SI7021(i2c)
ss = Seesaw(i2c, addr=0x36) #moisture board

# Wait for the sensor to be ready
while not ccs811.data_ready:
    print("\nAirqual sensor not ready")
    pass

while True:
	CST = pytz.timezone('US/Central')
	Now = datetime.now(CST)
	CO2 = ccs811.eco2
	TVOC = ccs811.tvoc
	RoomTemperature = sensor.temperature
	Humidity = sensor.relative_humidity
	SoilTemp = ss.get_temp()
	SoilMoisture = ss.moisture_read()

	sql = "INSERT INTO SensorData (MeasureTime,CO2,TVOC,RoomTemperature,Humidity,SoilTemperature,SoilMoisture) VALUES (%s, %s, %s, %s, %s, %s, %s)"
	val = (Now,CO2,TVOC,RoomTemperature,Humidity,SoilTemp,SoilMoisture)
	mycursor.execute(sql, val)

	mydb.commit()

	print("\n")
	print(Now)
	print("CO2: {} PPM, TVOC: {} PPB".format(ccs811.eco2, ccs811.tvoc))
	print("Temperature: %0.1f C" % sensor.temperature)
	print("Humidity: %0.1f %%" % sensor.relative_humidity)
	touch = ss.moisture_read() # read moisture level through capacitive touch pad
	temp = ss.get_temp() # read temperature from the soil temperature sensor (NOT soil temp, it is ambient on the chip)
	print("Soil Sensor Ambient Temp: " + str(temp) + "  Moisture: " + str(touch))

	fromaddr = "FROMEMAIL"
	toaddr = "TOEMAIL"
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddr

	msg['Subject'] = "Plant Status"
	body = "This is your plant status at: \n" + str(Now) + "\nCO2 (PPM): " + str(CO2) + "\nTVOC (PPB): " + str(TVOC) + "\nRoom Temperature (C): " + str(RoomTemperature) + "\nHumidity (%): " + str(Humidity) + "\nSoil Temperature (C): " + str(SoilTemp) + "\nSoil Moisture: " + str(SoilMoisture) + "\n\nPlease continue to monitor your plant to ensure healthy growth.\n\nThank you from the DFW Plant Monitoring Team!"
	msg.attach(MIMEText(body, 'plain'))
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(fromaddr, "FROMEMAILPASSWORD")
	text = msg.as_string()
	server.sendmail(fromaddr, toaddr, text)
	server.quit()

	if (touch < 600):

		msg['Subject'] = "Plant Status: Moisture Low"
		body = "The soil moisture of the plant is: " + str(touch) + "\nPlease water the plant immediately."
		msg.attach(MIMEText(body, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(fromaddr, "FROMEMAILPASSWORD")
		text = msg.as_string()
		server.sendmail(fromaddr, toaddr, text)
		server.quit()

	elif (RoomTemperature > 25.5):

		msg['Subject'] = "Plant Status: Temperature High"
		body = "The room temperature is: " + str(SoilMoisture) + "\nPlease ensure room temperature is below 25.5C for healthy plant life."
		msg.attach(MIMEText(body, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(fromaddr, "FROMEMAILPASSWORD")
		text = msg.as_string()
		server.sendmail(fromaddr, toaddr, text)
		server.quit()

	time.sleep(1800)