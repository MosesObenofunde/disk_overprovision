from google.cloud import container_v1
from httplib2 import Http 
from datetime import datetime
from pprint import pprint
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery, errors
from pytz import timezone
import base64
import json
import googleapiclient.discovery
import logging
import os
import time
import requests


format = "%Y-%m-%d %H:%M:%S"
now_utc = datetime.now(timezone('UTC'))
slack = now_utc.astimezone(timezone('Asia/Kolkata'))
for_slack= slack.strftime(format)
# for_slack =(now.strftime("%d %b %Y %X"))

PROJECT = os.getenv("project")
logging.basicConfig(level=logging.INFO)
WEB_HOOK = os.getenv("webhook")


def hello_pubsub(event, context):
    try:
        logging.info("Decode: {}".format(event))
        pubsub_message=(base64.b64decode(event['data']).decode('utf-8'))
        print(pubsub_message)
        json_string = json.loads(pubsub_message)
        logging.info("Event: {}".format(json_string))

        #owner=(json_string['protoPayload']['authenticationInfo']['principalEmail'])
        # own=(str(owner).split('@')[0]).replace('.','_')
        
        # # resource_name=(json_string['protoPayload']['request']['name'])
        methodName=(json_string['protoPayload']['methodName'])

        logging.info("Method called is {}".format(methodName))

        if 'compute.instances' in methodName:
            instance_tag(json_string)

        if 'CreateCluster' in methodName:
            gke_cluster(json_string)

        if 'disks' in methodName:
            disk_tags(json_string)    


    except Exception as e:
        print("Inside Exception")  
        print (e)    


def slack_notify(resource_name,own,region,size):
    disksize=size
    owner=own
    disk_name=resource_name
    region =region
    post = {"attachments":[{"color":"#ff0000","blocks":[{"type":"section","text":{"type":"mrkdwn","text":"Issue found:\n*Disk Size Greater than 50GB Created*"}},{"type":"section","fields":[{"type":"mrkdwn","text":"*Resource Name:*\n {}".format(disk_name)},{"type":"mrkdwn","text":"*Priority:*\n `HIGH`"},{"type":"mrkdwn","text":"*Created On:*\n{}".format(for_slack)},{"type":"mrkdwn","text":"*Owner:*\n {}".format(owner)},{"type":"mrkdwn","text":"*GCP Account:*\n {}".format(PROJECT)},{"type":"mrkdwn","text":"*Disk Size:*\n {} GB".format(disksize)},{"type":"mrkdwn","text":"*Disk Region:*\n {}".format(region)}]},{"type":"divider"}]}]}
    json_data = json.dumps(post)
    try:
        req = requests.post(WEB_HOOK, data=json_data)
        print(req)
    except Exception as e:
        print(e)  

def instance_tag(json_string):
    logging.info("Inside Instance Create")
    logging.info(json_string)
    region=(json_string['protoPayload']['resourceLocation']['currentLocations'][0])
    resource_name=(json_string['protoPayload']['request']['name'])
    own=(json_string['protoPayload']['authenticationInfo']['principalEmail'])
    # Listing out the disk attached to the instance    
    len_disk=(len(json_string['protoPayload']['request']['disks']))
    print(len_disk)
    for i in range(0,len_disk):
        disk_name=(json_string['protoPayload']['request']['disks'][i]['deviceName'])
        disk_size=(json_string['protoPayload']['request']['disks'][i]['initializeParams']['diskSizeGb'])
        if int(disk_size) > 50:
            if (disk_name == 'persistent-disk-0'):
                logging.info("{} is created form GKE cluster.".format(disk_name))
            else:
                logging.info("{} is greater than threshold invoking slack msg.".format(disk_name))
                slack_notify(disk_name,own,region,disk_size)
       

def gke_cluster(json_string):
    print("Inside GKE Cluster Create")
    client = container_v1.ClusterManagerClient()
    cluster_name=(json_string['resource']['labels']['cluster_name'])
    region = (json_string['resource']['labels']['location'])
    response = client.get_cluster(project_id=PROJECT,zone=region,cluster_id=cluster_name)
    # print(response) 
    try:
        if int(response.node_config.disk_size_gb) > 50:
            
            disk_name="Disk of GKE Cluster: "+str(response.name)
            disk_size=response.node_config.disk_size_gb
            own="GKE Cluster: "+str(response.name)
            logging.info("{} is greater than threshold invoking slack msg.".format(disk_name))
            slack_notify(disk_name,own,region,disk_size)
    except Exception as e:
        print(e)


def disk_tags(json_string):
    region=(json_string['protoPayload']['resourceLocation']['currentLocations'][0])
    own = (json_string['protoPayload']['authenticationInfo']['principalEmail'])
    disk_name=(json_string['protoPayload']['request']['name'])
    disk_size=(json_string['protoPayload']['request']['sizeGb'])
    if int(disk_size) > 50:
        logging.info("{} is greater than threshold invoking slack msg.".format(disk_name))
        slack_notify(disk_name,own,region,disk_size)