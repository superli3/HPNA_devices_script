#This script outputs a list of devices within a device group in HPNA into a csv file. I had quite a time figuring out how to do this in HP NA with the SOAP API, so this code is for anyone's reference. Hope it helps whoever needs it!

import os
import pprint
import urllib3
import logging
import argparse
import json
import csv
import datetime
import pprint
from dateutil.parser import *

from collections import OrderedDict
from credential import sn, pw
from requests import Session
from zeep import Client, Settings, helpers
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken

#python -mzeep https://hpna_url_here/soap?wsdl --no-verify <- use this command to view WSDL file for HPNA. You will need to replace the HPNA url with your actual URL.
 
#Disable InsecureRequestWarning: Unverified HTTPS request is being Made.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)
 
 
console_handler = logging.StreamHandler() # sys.stderr
console_handler.setLevel(logging.CRITICAL) # set later by set_log_level_from_verbose() in interactive sessions
console_handler.setFormatter( logging.Formatter('[%(levelname)s](%(name)s): %(message)s') )
logger.addHandler(console_handler)
 
parser = argparse.ArgumentParser(description='Retrieve diagnostics from HPNA')
parser.add_argument('-v', '--verbose', action="count", help="verbose level... repeat up to three times.")

def set_log_level_from_verbose(args):
	if not args.verbose:
		console_handler.setLevel('ERROR')
	elif args.verbose == 1:
		console_handler.setLevel('WARNING')
	elif args.verbose == 2:
		console_handler.setLevel('INFO')
	elif args.verbose >= 3:
		console_handler.setLevel('DEBUG')
	else:
		logger.critical("UNEXPLAINED NEGATIVE COUNT!")
 
args = parser.parse_args()
set_log_level_from_verbose(args)
 
 
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


# Define where HP NA is and the user credentials
wsdl = 'https://hpna_url_here/soap?wsdl'
hp_user = 'user_name_string'
hp_password = 'password_string'
 
logger.info('Setup and collect WSDL')
session = Session()
session.verify = False
transport = Transport(session = session)
logger.debug('Transport parameters: %s', transport)
client = Client(wsdl = wsdl,transport = transport)
logger.debug('Client : %s', client)
logger.info('WSDL session complete')

# Map the WSDL to the actual HPNA host. The WSDL file will point the services at localhost... this mapping repoints to the
# real server with the services
service = client.create_service('{http://hp.com/nas/10/20}NetworkManagementApiBinding', 'https://hpna_url_here/soap')


# Perform a user login and get a session id we can use for future requests
# first we get the data class ready to fill
userinfo = client.get_type('ns0:loginInputParms')
 
logger.debug('loginInputParms empty parameters: %s', userinfo)
 
# secondly we fill the data class with the required information
user = userinfo(username = sn, password = pw )
 
logger.debug('loginInputParms filled parameters: %s', user)

# thirdly we call the service with the appropriate service name 'login'
# service names are found in the WSDL 'Service: NetworkManagementApi' - line 706 onwards
# notice we call via 'service' and not 'session' - 'service' contains the mapped WSDL

session_id = service.login(user)
logger.info('session_id: %s', session_id.Text)

device_class = client.get_type ( 'ns0:list_deviceInputParms'
	 )
#Insert Group that you want here
device = device_class ( sessionid = session_id.Text, group = 'Insert Group'
	 )
devices = service.list_device ( device
	 )

input_dict = helpers.serialize_object(devices.ResultSet.Row)
output_dict = json.loads(json.dumps(input_dict))
print(type(output_dict))
outfile = open ('hpna.csv', 'w', newline='')
csv_writer = csv.writer(outfile)

header = output_dict[0].keys()
csv_writer.writerow(['hostName', 'DeviceType', 'model','primaryIPAddress','Source'])

#outfile = output_dict.writerow(output_dict[0][0].keys())
for row in output_dict:
	hostName = row['hostName']
	model = row['model'] #Device Model 
	primaryIPAddress = row['primaryIPAddress'] #IP Address
	lastAccessAttemptDate = row['lastAccessAttemptDate'] #LastAccessAttemptDate - keep if within last 7 days
	lastAccessAttemptStatus = row['lastAccessAttemptStatus']
	lastAccessSuccessDate = row['lastAccessSuccessDate']
	Source = 'HPNA'
			
	if lastAccessAttemptDate is None:
		lastAccessAttemptDate2 = lastAccessAttemptDate
	else: 
		lastAccessAttemptDate2 = parse(lastAccessAttemptDate, ignoretz=True)
		
	if lastAccessSuccessDate is None:
		lastAccessSuccessDate2 = lastAccessSuccessDate
	else: 
		lastAccessSuccessDate2 = parse(lastAccessSuccessDate, ignoretz=True)
	
	
	today = datetime.datetime.now() #today's date
	if lastAccessSuccessDate2 is not None and (lastAccessSuccessDate2).date() >= (today - datetime.timedelta(days=7)).date():
		csv_writer.writerow([hostName, DeviceType, model, primaryIPAddress, Source]) #values row
	else:
		continue
	

print("HPNA Scraping Complete")	

exit(0)
