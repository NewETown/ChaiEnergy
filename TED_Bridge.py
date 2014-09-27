import datetime
import requests


def fetch_data():
	#fetch data
	# ted configurations
	MTU_ID = 0
	datapoints_back_in_time = 100
	starting_datapoint = 0
	url = "http://10.120.230.128/history/secondhistory.xml?MTU=" + str(MTU_ID) + "&COUNT=" + str(datapoints_back_in_time) + "&INDEX=" + str(starting_datapoint)

	TED_api_request = requests.get(url)

	return TED_api_request.text


def parse_ted_response(xml_data):
	# Parse XML
	# Sample XML from TED device
	#	<History>
	# 	<SECOND><MTU>0</MTU><DATE>09/24/2014 13:21:53</DATE><POWER>2</POWER><COST>1</COST><VOLTAGE>1206</VOLTAGE></SECOND>
	#	</History>

	import xml.etree.ElementTree as ET
	root = ET.fromstring(xml_data)
	all_data = [];
	for second in root.findall('SECOND'):
		all_powers = second.findall('POWER')
		all_dates = second.findall('DATE')

		if (len(all_powers)>0 and len(all_dates) > 0):
			power = None
			date = None

			power = all_powers[0]
			date = all_dates[0]

			power_as_int = int(power.text)
			date_as_date = datetime.datetime.strptime(date.text, "%m/%d/%Y %H:%M:%S")

			all_data.append({"power":power_as_int,"date":date_as_date})
	return all_data

def remove_already_posted_data(datapoints):

	# filter data
	last_successfully_posted_data = datetime.datetime.fromtimestamp(0)

	unposted_data = [i for i in datapoints if i["date"] >last_successfully_posted_data]
	return unposted_data
def format_data_to_post(datapoints):
	# form data to post
	from uuid import getnode as get_mac
	mac_id = ':'.join(hex(get_mac())[i:i+2] for i in range(2,14,2))
	device = "ted5000"

	# 	postring format
	# 	{mac_id : hex, "device" : ted5000, power: float, time: string}
	data_to_post = []
	for datapoint in datapoints:
		time = 	datetime.datetime.strftime(datapoint["date"], "%m/%d/%Y %H:%M:%S")
		power = datapoint["power"]
		data_to_post.append({"mac_id":mac_id,"device":device,"time":time,"power":power})
	
	return data_to_post

def post_data(data):
	#posting
	import json
	post_url = "http://ted.chaienergy.net"

	datapoint_to_post = data[0]
	json_datapoint_to_post = json.dumps(datapoint_to_post)
	print "request: " + json_datapoint_to_post
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
	data_post_response = requests.post(post_url, data=json.dumps(json_datapoint_to_post), headers=headers)
	print "response: " + data_post_response.content
	if (data_post_response.status_code==200):
		print "success"
	else:
		print "failure"


if __name__ == "__main__":
	import time
	while(True):
		try:
			fetched_data = fetch_data()
			datapoints = parse_ted_response(fetched_data)
			datapoints = remove_already_posted_data(datapoints)
			post_data(format_data_to_post(datapoints))
			time.sleep(2)
		except Exception, error: 
			print "error: " + error