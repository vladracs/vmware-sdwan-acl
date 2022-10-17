#!/usr/bin/env python3
#
# Author: vfrancadesou@vmware.com
# Leveraging cisco-acl from another Vladimir https://github.com/vladimirs-git/cisco-acl
#
# Not to be considered as best practices in using VMware VCO API
# Meant to be used in Lab environments - Please test it and use at your own risk
#
# Convert Cisco ACL - without groups - to VMware SD-WAN firewall rules 
# 
# For lines with destination operator = eq, when multiple destinatio ports are listed, 
# these are grouped and converted in an Vmware sd-wan object-group (address and port)
# # 
# current version does not support:
#  grouping of source ports - ie 1 line will be created for each source port in a line
#  operator = "neq"
# 
# Note that VMware SDWAN Firewall rules only apply to outbound direction
# ie as it stand this script should only be used in ACLs used at outgoing direction.
# 
# 
# please note that VMWare API and Support team - do not guarantee this samples
# It is provided - AS IS - i.e. while we are glad to answer questions about API usage
# and behavior generally speaking, VMware cannot and do not specifically support these scripts
#
# Compatible with api v1 of the vmware sd-wan vco api
# using tokens to authenticate
#
#
from fileinput import lineno
from pprint import pprint
import cisco_acl
import os
import sys
import requests
import json
import copy
import argparse
import csv
from copy import deepcopy
######### VELO VARIABLES AND FUNCTIONS

########## VCO info and credentials
# Prefer to use OS environments to hold token variable
token = "Token %s" %(os.environ['VCO_TOKEN'])
headers = {"Content-Type": "application/json", "Authorization": token}
VCO_FQDN=os.environ['VCO_HOSTNAME']
token = os.environ['VCO_TOKEN']
vco_url = 'https://' + VCO_FQDN + '/portal/rest/'

######## VCO API methods
get_enterprise = vco_url + 'enterprise/getEnterprise'
get_edgelist = vco_url+'enterprise/getEnterpriseEdgeList'
get_edgeconfig = vco_url + 'edge/getEdgeConfigurationStack'
get_edgeoverview = vco_url + 'enterprise/getEnterpriseEdges'
update_edgeconfig = vco_url+'configuration/updateConfigurationModule'
edge_prov = vco_url+'edge/edgeProvision'
get_profiles =vco_url + 'enterprise/getEnterpriseConfigurations'
create_profile = vco_url+'configuration/cloneEnterpriseTemplate'
insert_module = vco_url+'configuration/insertConfigurationModule'
getObjectGroups = vco_url+'enterprise/getObjectGroups'
updateObjectGroup = vco_url+'enterprise/updateObjectGroup'
insertObjectGroup = vco_url+'enterprise/insertObjectGroup'

global lineno

########
#### RETRIEVE ENTERPRISE ID for this user
def find_velo_enterpriseId():
	#Fetch enterprise id convert to JSON
    eid=0
    resp = requests.post(get_enterprise, headers=headers, data='')
    respj = resp.json()
    error=str(respj.get('error'))
    if 'None'in error:
        eid=respj['id']
        print('Enterprise Id = %d'%(eid))
        return eid
    else: 
        print(respj)
        go=False
        while go==False:
            a = input("ERROR - Enter [yes/no] to continue: ").lower()
            if a=="yes":
                go=True
                continue
            elif a=="no":
                sys.exit(0)
            else:
                    print("Enter either yes/no: ")
    

#############

##### Find Edge in the list
def search_name(name,listName):
    for p in listName:
        if p['name'] == name:
            return p

def get_template_rule(module):
    rules = module['data']['segments'][0]['outbound']
    return [rule for rule in rules if rule['name'] == 'AllowAny'][0]


global i,j,k
global sip,ssm,dip,dsm,srcport,dstport,proto,sport_high,sport_low

def create_pgroup(proto,list_ports):
    list_obj=[{"proto":proto,"port_low":list_ports[0],"port_high":list_ports[0]}]
    t=1
    while (len(list_ports)>t):
        obj={"proto":proto,"port_low":list_ports[t],"port_high":list_ports[t]}
        list_obj.append(obj)
        t=t+1

    print(list_obj)
    params = {
                        'enterpriseId': eid,
                        'description': "ace parsed line n."+str(lineno),
                        'name': "pg."+str(lineno),
                        'type': "port_group",
                        'data': list_obj
                }
    resp = requests.post(insertObjectGroup, headers=headers, data=(json.dumps(params)))
    #{"jsonrpc":"2.0","result":{"id":75518,"rows":1},"id":30}
    #{'error': {'code': -32603, 'message': 'Name must be Unique'}}
    respj = resp.json()
    error=str(respj.get('error'))
    if 'None'in error:
         print('Created Port-Group = pg.',i+1)
         pgid = respj['id']
         
    else: 
        print(respj)
        go=False
        while go==False:
            a = input("ERROR - Enter [yes/no] to continue: ").lower()
            if a=="yes":
                go=True
                continue
            elif a=="no":
                sys.exit(0)
            else:
                    print("Enter either yes/no: ")
    # Retrieve logical id for newly created pg
    params = {'enterpriseId': eid,"type":"port_group"}
    resp = requests.post(getObjectGroups, headers=headers, data=json.dumps(params))
    vcogroups=resp.json()
   
    for group in vcogroups:
        if (group['id']==pgid): 
            return(group["logicalId"])      
   
def create_agroup(dip,dsm):
    #{"jsonrpc":"2.0","method":"enterprise/insertObjectGroup","params":{"name":"ag1","description":"","type":"address_group","data":[{"ip":"10.10.10.0","rule_type":"netmask","mask":"255.255.255.0"}]},"id":28}
    list_obj=[{"ip":dip,"rule_type":"netmask","mask":dsm}]
    params = {
                        'enterpriseId': eid,
                        'description': "ace parsed line n."+str(lineno),
                        'name': "ag."+str(lineno),
                        'type': "address_group",
                        'data': list_obj
                }
    resp = requests.post(insertObjectGroup, headers=headers, data=(json.dumps(params)))
    #{"jsonrpc":"2.0","result":{"id":75518,"rows":1},"id":30}
    #{'error': {'code': -32603, 'message': 'Name must be Unique'}}
    respj = resp.json()
    error=str(respj.get('error'))
    if 'None'in error:
         print('Created Address Group = ag.',i+1)
         pgid = respj['id']
    else: 
        print(respj)
        go=False
        while go==False:
            a = input("ERROR - Enter [yes/no] to continue: ").lower()
            if a=="yes":
                go=True
                continue
            elif a=="no":
                sys.exit(0)
            else:
                    print("Enter either yes/no: ")
    # Retrieve logical id for newly created pg
    params = {'enterpriseId': eid,"type":"address_group"}
    resp = requests.post(getObjectGroups, headers=headers, data=json.dumps(params))
    vcogroups=resp.json()
   
    for group in vcogroups:
        if (group['id']==pgid): 
            return(group["logicalId"])      

def destinations(proto,sip,ssm,sport_low,sport_high):
                
    #DESTINATION
                skip=False
                dstport=data["items"][i]["dstport"]["ports"]

                if (data["items"][i]["dstaddr"]["prefix"]=="0.0.0.0/0"):
                    dip = "any"
                    dsm = "255.255.255.255"
                else:
                    dsubnet_mask=data["items"][i]["dstaddr"]["subnet"].split(" ")
                    dip = dsubnet_mask[0]
                    dsm = dsubnet_mask[1]
               

                if(data["items"][i]["dstport"]["operator"]==""):
                    dport_high=-1
                    dport_low=-1
                    
                elif(data["items"][i]["dstport"]["operator"]=="gt"):
                    dport_high=65535
                    dport_low=dstport[0]+1
                   
                elif(data["items"][i]["dstport"]["operator"]=="lt"):
                        np=data["items"][i]["dstport"]["sport"].split("-")
                        dport_high=np[1]
                        dport_low=2 ### VMware SDWAN only take ports starting at 2
                   
                elif(data["items"][i]["dstport"]["operator"]=="range"):
                        range=data["items"][i]["dstport"]["sport"].split("-")
                        r1 = range[0]
                        r2 = range[1]
                        dport_high=r2
                        dport_low=r1       
                elif('eq' in data["items"][i]["dstport"]["operator"].split()):
 #  REPEATING FOR EACH DST PORT
                    skip=True
                    if(action=="permit"): new_rule['action']['allow_or_deny'] = 'allow'
                    if(action=="deny"): new_rule['action']['allow_or_deny'] = 'drop'
                    new_rule['name'] = data["name"]+"."+str(i+1)
                    new_rule['match']['s_rule_type'] = 'prefix'
                    new_rule['match']['d_rule_type'] = 'prefix'
                    new_rule['match']['proto'] = proto
                    new_rule['match']['sip']= sip
                    new_rule['match']['ssm']= ssm
                    new_rule['match']['sport_low'] = sport_low
                    new_rule['match']['sport_high'] = sport_high
                    if (len(dstport)==1):
                     new_rule['match']['dip']= dip
                     new_rule['match']['dsm']= dsm
                     new_rule['match']['dport_low'] = dstport[0]
                     new_rule['match']['dport_high'] = dstport[0]
                    else:
                        dPortGroup=create_pgroup(proto,dstport)
                        dAddressGroup=create_agroup(dip,dsm)
                        new_rule['match']['dPortGroup']=dPortGroup
                        new_rule['match']['dAddressGroup']=dAddressGroup
                    if len(edge_firewall_module_data['segments']) == 0:
                            edge_firewall_module_data['segments'].append({ 'outbound': [] })
                    edge_firewall_module_data['segments'][0]['outbound'].append(deepcopy(new_rule))
                    #print(edge_firewall_module_data['segments'][0]['outbound'])
                    #print("operator not eq")
                    # Make update call
                    params = {
                    'enterpriseId': eid,
                    'id': edge_firewall_module_id,
                    '_update': {
                    'data': edge_firewall_module_data
                    }
                    }
                    resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params)))
                    respj = resp.json()
                    error=str(respj.get('error'))
                    if 'None'in error:
                            print('Appended rule n.',i+1)
                            print()
                    else: 
                        
                        go=False
                        while go==False:
                            a = input("ERROR - Enter [yes/no] to continue: ").lower()
                            if a=="yes":
                                go=True
                                continue
                            elif a=="no":
                                sys.exit(0)
                            else:
                                    print("Enter either yes/no: ")
                                     
                if(skip==False):
                    ####
                        if(action=="permit"): new_rule['action']['allow_or_deny'] = 'allow'
                        if(action=="deny"): new_rule['action']['allow_or_deny'] = 'drop'
                        new_rule['name'] = data["name"]+"."+str(i+1)
                        new_rule['match']['s_rule_type'] = 'prefix'
                        new_rule['match']['d_rule_type'] = 'prefix'
                        new_rule['match']['proto'] = proto
                        new_rule['match']['sip']= sip
                        new_rule['match']['ssm']= ssm
                        new_rule['match']['sport_low'] = sport_low
                        new_rule['match']['sport_high'] = sport_high
                        new_rule['match']['dip']= dip
                        new_rule['match']['dsm']= dsm
                        new_rule['match']['dport_low'] = dport_low
                        new_rule['match']['dport_high'] = dport_high   
                        if len(edge_firewall_module_data['segments']) == 0:
                            edge_firewall_module_data['segments'].append({ 'outbound': [] })
                        edge_firewall_module_data['segments'][0]['outbound'].append(deepcopy(new_rule))
                        # Make update call
                        params = {
                        'enterpriseId': eid,
                        'id': edge_firewall_module_id,
                        '_update': {
                        'data': edge_firewall_module_data
                        }
                        }
                        resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params)))
                        respj = resp.json()
                        error=str(respj.get('error'))
                        if 'None'in error:
                              print('Appended rule n.',i+1)
                              print()
                        else: 
                            print(respj)
                            go=False
                            while go==False:
                                a = input("ERROR - Enter [yes/no] to continue: ").lower()
                                if a=="yes":
                                    go=True
                                    continue
                                elif a=="no":
                                    sys.exit(0)
                                else:
                                        print("Enter either yes/no: ")
                                     


######################### Main Program #####################
#### MAIN BODY
######################### Main Program #####################

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--edge", help="edge name",required=True)
#parser.add_argument('EdgeSource')
#parser.add_argument('EdgeDest')
#parser.add_argument('Map')
args = parser.parse_args()
EdgeSrcName=args.edge
eid = find_velo_enterpriseId()

	# Find Source Edge id based on Edge name
params = {'enterpriseId': eid}
edgesList = requests.post(get_edgelist, headers=headers, data=json.dumps(params))
eList_dict=edgesList.json()

#### Find Source Edge
name=search_name(EdgeSrcName, eList_dict)
if (str(name)=='None'):
    print('Source Edge '+EdgeSrcName+' not found!')
    go=False
    while go==False:
        a = input("Enter [yes/no] to continue: ").lower()
        if a=="yes":
            go=True
            continue
        elif a=="no":
            sys.exit(0)
        else:
            print("Enter either yes/no: ")
else:
    edid = name['id']
    print ('Source Edge: '+EdgeSrcName+' found on VCO with Edge id: '+str(edid))

params = {'edgeId': edid}
Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
stack=Edge_Config.json()
edge_specific_profile = stack[0]
profile = stack[1]

edge_firewall_module_id = None
edge_firewall_module_data = None

profile_firewall_module = [module for module in profile['modules'] if module['name'] == 'firewall'][0]
# Get Edge firewall module (note that this may not exist for new Edges)
#print("Profile Firewall Module data")#
#print(profile_firewall_module['data'])

tmp = [module for module in edge_specific_profile['modules'] if module['name'] == 'firewall']
#print("Edge Firewall Module Data")
#print(len(tmp[0]['data']))
if (len(tmp) > 0):
    edge_firewall_module_id = tmp[0]['id']
    edge_firewall_module_data = tmp[0]['data']
    print()

    ##print(edge_firewall_module_data)
    #print(edge_firewall_module_id)
else:

    # We need to create an Edge-specific firewall module instance if one doesn't already exist
    print("Inserting FW module at Edge Override")
    edge_firewall_module_data = deepcopy(profile_firewall_module['data'])
    #print(edge_firewall_module_data)
    params = {
        'enterpriseId': eid,
        'configurationId': edge_specific_profile['id'],
        'name': 'firewall',
        'data': edge_firewall_module_data
    }
    result = requests.post(insert_module, headers=headers, data=(json.dumps(params)))
    #print(result.json())

#if module is there but not data!?
if (len(edge_firewall_module_data)==0):
    print()
    print("Inserting data from Profile")
    edge_firewall_module_data=profile_firewall_module['data']
    d={"data":{}}
    d['data']=edge_firewall_module_data
    params = {"enterpridId": eid,
         "configurationModuleId" : edge_firewall_module_id,
         "returnData" : 'true',
         "_update":  d,
        }
    resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params)))
    print('Firewall Rules updated')
print()


#### Processing ACL and mapping to VCO FW config fields

config = """
hostname HOSTNAME

ip access-list extended ACL_NAME
  permit tcp any 10.20.210.30 0.0.0.1 eq 8443
  permit tcp any host 10.10.100.90 eq www 443
  permit tcp any 10.50.150.12 0.0.0.1 eq 139 445
  permit tcp any eq 65001 192.168.24.0 0.0.0.255 eq 139 445
  permit tcp any 172.16.50.32 0.0.0.31 gt 1024
  permit udp 10.12.0.0 0.0.255.255 eq 65000 host 10.60.200.100 eq domain
  permit tcp 10.25.0.0 0.0.255.255 host 10.50.110.57 eq 3000 3001 3002
  permit tcp any host 10.13.1.1 range 1521 1526
  permit ip any host 10.20.70.111
  permit tcp any any lt 1024
  deny udp any lt 1024 any
  deny tcp any range 80 81 any
  
  
interface Ethernet1
  ip access-group ACL_NAME in
  ip access-group ACL_NAME out
"""
f = open("cisco-config.txt")

config = f.read()

f.close()

print(config)


# Create ACL, TCP/UDP ports and IP protocols as well-known names
acls = cisco_acl.acls(config=config, platform="ios")
acl = acls[0]

# Convert well-known TCP/UDP ports and IP protocols to numbers
# Note, ftp -> 21, telnet -> 23, icmp -> 1
acl.protocol_nr = True
acl.port_nr = True
# Convert ACL to dictionary
global data
data = acl.data()


i=0
for items in data["items"]:
 new_rule = {"name":"AllowAny","match":{"appid":-1,"classid":-1,"dscp":-1,"sip":"any","smac":"any","sport_high":-1,"sport_low":-1,"ssm":"any","svlan":-1,"os_version":-1,"sInterface":"","hostname":"","dip":"any","dport_low":-1,"dport_high":-1,"dsm":"any","dvlan":-1,"dInterface":"","proto":-1,"s_rule_type":"netmask","d_rule_type":"prefix"},"action":{"allow_or_deny":"skip"}}

 print("ACE line n.",i+1)
 lineno=i+1

    #check if line can be processed
 if (len(data["items"][i]["srcaddr"]["prefix"])!=0):
    srcport=data["items"][i]["srcport"]["ports"]
    action=data["items"][i]["action"]
    proto= data["items"][i]["protocol"]["number"]
    if (data["items"][i]["srcaddr"]["prefix"]=="0.0.0.0/0"):
      sip = "any"
      ssm = "255.255.255.255"
    else:
     ssubnet_mask=data["items"][i]["srcaddr"]["subnet"].split(" ")
     sip = ssubnet_mask[0]
     ssm = ssubnet_mask[1]
     #PROCESS SORCE PORTS ######
    skip=False
    
    if(data["items"][i]["srcport"]["operator"]==""):
     sport_high=-1
     sport_low=-1
   
    elif(data["items"][i]["srcport"]["operator"]=="gt"):
         sport_high=65535
         sport_low=srcport[0]+1
        
    elif(data["items"][i]["srcport"]["operator"]=="lt"):
        np=data["items"][i]["srcport"]["sport"].split("-")
        sport_high=np[1]
        sport_low=2 ### VMware SDWAN only take ports starting at 2
   
    elif(data["items"][i]["srcport"]["operator"]=="range"):
        range=data["items"][i]["srcport"]["sport"].split("-")
        r1 = range[0]
        r2 = range[1]
        sport_high=r2
        sport_low=r1
        
    elif('eq' in data["items"][i]["srcport"]["operator"].split()):
            #add each destination for each of the sort ports found in the line - this can get big
            for ports in srcport:
                sport_high=ports
                sport_low=ports
                destinations(proto,sip,ssm,sport_low,sport_high)
            skip=True
    if(skip==False):
         destinations(proto,sip,ssm,sport_low,sport_high)            
 else:
       print("cannot process this line")
  
 i=i+1
