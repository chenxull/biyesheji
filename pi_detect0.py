from imutils.video import VideoStream   #直接读取usb摄像头的数据
from pyimagesearch.tempimage import TempImage
import datetime
import argparse
import imutils
import time
import cv2
import warnings
import json
from bypy import ByPy
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

from DB import DBConnect
import smtplib
"""
reload(sys)
sys.setdefaultencoding('utf8')
conn = DBConnect.dbconnect()
cur = conn.cursor()
"""
conn = DBConnect.dbconnect()
cur = conn.cursor()
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
	help="path to the JSON configuration file")
ap.add_argument("-p", "--picamera", type=int, default=-1,
	help="whether or not the Raspberry Pi camera should be used")
args = vars(ap.parse_args())

warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def send_email():
    from_addr = "18119880788@163.com"
    password = "CHENxu19961017"
    to_addr = "947584280@qq.com"
    smtp_server = "smtp.163.com"

    msg = MIMEText('有非法人员出现，请确保家中财务安全...', 'plain', 'utf-8')
    msg['From'] = _format_addr('家庭监控系统 <%s>' % from_addr)
    msg['To'] = _format_addr('管理员 <%s>' % to_addr)
    msg['Subject'] = Header('有非法入侵者……', 'utf-8').encode()

    server = smtplib.SMTP(smtp_server, 25)
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()

def insert_data():
        global times
        d=datetime.datetime.now()
        times=d.strftime("%Y-%m-%d %H:%M:%S")
        id="01"
        status="Occupied"
        cur.execute("insert into room_status values('%s','%s','%s')"%(status,id,times))
        conn.commit()

def insert_images(img):
        cur.execute("insert into images values('%s')"%(img))
    
def video():
	vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
	print("[INFO] warming up...")
	time.sleep(2.0)
	avg = None
	lastUploaded = datetime.datetime.now()   #当前系统时间
	motionCounter = 0

	while True:
		frame = vs.read()
		timestamp = datetime.datetime.now()
		text = "Unoccupied"   
		
		frame = imutils.resize(frame,width=400)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray,(21,21),0)

		if avg is None:
			print("[INFO] starting background model...")
			avg = gray.copy().astype("float")
			cv2.destroyAllWindows()
			continue
			
			

		cv2.accumulateWeighted(gray, avg, 0.5)  #求gray的平均值并放入到avg中
		frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
		thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,cv2.THRESH_BINARY)[1] 
		thresh = cv2.dilate(thresh, None, iterations=2)
		cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)   
		cnts = cnts[0] if imutils.is_cv2() else cnts[1]

		for c in cnts:
		    if cv2.contourArea(c) < conf["min_area"]:
		    	continue
		    (x,y,w,h) = cv2.boundingRect(c)
		    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
		    text = "Occupied"

		ts = timestamp.strftime("%y-%m-%d %I:%M:%S")
		cv2.putText(frame, "room status: {}".format(text), (10, 20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
		cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,0.35, (0, 0, 255), 1)
		if text == "Occupied":
                    if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
                        motionCounter +=1
                        if conf["use_dropbox"]:
                            t = TempImage()
                            cv2.imwrite(t.path,frame)
                            print("[UPLOAD] {}".format(ts))
                            path = "/{base_path}/{timestamp}.jpg".format(
						    base_path=conf["dropbox_base_path"], timestamp=ts)
                            bp=ByPy()
                            send_email()
                            insert_data()
                            insert_images(t.path)
                            bp.upload(t.path,'/apps/')
                        lastUploaded = timestamp
                        motionCounter = 0
		else:
			motionCounter = 0
            
		if conf["show_video"]:
			cv2.imshow("Security Feed",frame)
			key = cv2.waitKey(1)& 0xFF
			if key == ord("q"):
				break
	cv2.destroyAllWindows()
	vs.stop()

if __name__ == '__main__':
	video()

























