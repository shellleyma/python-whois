#encoding=utf-8
import httpapi as api
import sendemail
import datetime
import random
import threading
try:
    from queue import Queue # py3
except ImportError:
    from Queue import Queue # py2
import time
from mylogger import get_logger
import mysql_python
from whois import whois
from whois import parser 
try:
    import configparser # py3
except ImportError:
    import ConfigParser as configparser # py2
import pytz
tz = pytz.timezone(pytz.country_timezones('cn')[0])

cf = configparser.ConfigParser()
cf.read("config.ini")

dllog = get_logger("success")
responselog = get_logger("response")
errorlog = get_logger("error")
orederlog = get_logger("domains_orders")

userid=cf.get("resellerclub", "userid")
apikey=cf.get("resellerclub", "apikey")
mysqlhost=cf.get("db", "mysqlhost")
mysqluser=cf.get("db", "mysqluser")
mysqlpass=cf.get("db", "mysqlpass")
mysqldb=cf.get("db", "mysqldb")


mail_to="shelleymxd@163.com,71413364@qq.com,wang2010xiang@foxmail.com"

#最初版本适用，后来从数据库读取相关数据，以下变量变成数据库读取值失败后的最后默认值
NS=["dawn.ns.cloudflare.com","rick.ns.cloudflare.com"]
customer_id=15058690
contact_id="54918903"
contact_id_array="54918903,54918836,54918834,54918816,54918720,54916505".split(',')


class DomainTaskTest(object):
    def __init__(self, threads_num=50, proxies=None,test=True):
        self.proxies = proxies

        self.test=test
        self.domain_queue= Queue()
        self.domain_list=[]
        self.threads_num = threads_num
        self.file="list.txt"
        # now=
        self.start_time=datetime.datetime.now(tz).replace(hour=3,minute=58,second=0,microsecond=0)
        self.end_time=self.start_time+datetime.timedelta(minutes=25)
        # self.end_time=datetime.datetime.now(tz).replace(hour=5,minute=0,second=0,microsecond=0)
    def get_domain_list_from_mysql(self):
        try:
            print("####start get domain list from mysql###")
            connect_mysql = mysql_python.MysqlPython(mysqlhost, mysqluser, mysqlpass, mysqldb)
            
            # sql_query = 'SELECT domain.domain,domain.customer_id,user.customer_id,domain.contact_id,user.default_contact_id,domain.ns1,domain.ns2,user.default_ns1,user.default_ns2,domain.username FROM domain as domain inner join user as user on user.username = domain.username AND domain.date >= %s Order by domain.inserttime'
            
            # sql_query = 'SELECT domain.domain,domain.customer_id,membership.customer_id,domain.contact_id,membership.default_contact_id,domain.ns1,domain.ns2,membership.default_ns1,membership.default_ns2,domain.username FROM domain as domain inner join membership on membership.user_name = domain.username AND domain.date = %s Order by LENGTH(domain.domain),domain.inserttime'
            sql_query = 'SELECT domain from domain where domain.date=%s group by domain'
            # print (datetime.datetime.now(tz))
            today=datetime.datetime.now(tz).strftime('%Y-%m-%d')
    
            print ("today is ",str(today))
            result = connect_mysql.select_advanced(sql_query, ('domain.date', str(today)))
            # domain_queue= Queue()
            print(len(result))
            for record in result:
                      #one[5]=record[-1]
                self.domain_list.append(record)
    
            print (self.domain_list)
                
    
        except Exception as e:
            print (str(e))
        pass 
    def check_domain_available(self,domain_name):
        

        # print( dir(whois))
        # domain = "esencia.in"
        w = whois(domain_name)
        t = w.query(False)
        p = parser.Parser(domain_name, t[1], t[0], True)

        try:

            # print( p.text)
            result=p.parse()

            print("######################")
            print(domain_name)

            if "NotFound" not in result:
            
                print ("Registrar:",list(result['Registrar']))
                print ("RegistrantID:",list(result['RegistrantID']))
                print ("CreationDate:",list(result['CreationDate']))
                print ("ExpirationDate",list(result['ExpirationDate']))
                print ("UpdateDate",list(result['UpdatedDate']))
                print ("RegistrantEmail:",list(result['RegistrantEmail']))

        except Exception as e:
            print(str(e))


    def get_today_domains(self):
        ins=api.ApiClient(userid, apikey, customer_id, contact_id, self.proxies,self.test)


        try:
            
            result=ins.domains_search( no_of_records=500, page_no=1, oreder_by=['creationtime'], order_id=None, reseller_id=None, customer_id=None, show_child_orders=None, product_key=None, status=['Active'], domain_name=None, privacy_enabled=None, creation_date_start=self.start_time.timestamp(), creation_date_end=self.end_time.timestamp(), expiry_date_start=None, expiry_date_end=None)
            # print(result,'\n')
            print(result['recsonpage'])
            if int(result['recsonpage'])>0:
                for i in range(0,int(result['recsonpage'])):
                    print (datetime.datetime.fromtimestamp(int(result[str(i+1)]['orders.creationtime']),tz=tz),result[str(i+1)]['entity.description'],result[str(i+1)]['entity.customerid'],result[str(i+1)]['entitytype.entitytypename'])

                    orederlog.info(str(datetime.datetime.fromtimestamp(int(result[str(i+1)]['orders.creationtime']),tz=tz))+"  "+result[str(i+1)]['entity.description']+"  "+result[str(i+1)]['entity.customerid']+"  "+result[str(i+1)]['entitytype.entitytypename'])
                    # print ('########')

            # print(len(result))
        except Exception as e:
            print (str(e))
    def run(self):
        self.get_domain_list_from_mysql()
        if (self.domain_list)==False:
            return
        for domain in  self.domain_list:
            try:
                self.check_domain_available(domain)
            except Exception as e:
                print(str(e))

                

def test():
    # proxies = {"http": "http://139.255.39.147:8080"}
    dl = DomainTaskTest(test=False)
    dl.run()

if __name__ == "__main__":
    test()
