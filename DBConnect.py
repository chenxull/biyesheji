import pymysql
def dbconnect():
	conn = pymysql.connect(host='localhost',port=3306,user='root',passwd='newPwd',db='FRT',charset="utf8")
	return conn
