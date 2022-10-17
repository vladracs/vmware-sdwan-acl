# vmware-sdwan-acl

python script that reads a cisco config file using the cisco-acl "library", and uses the result dictionary to build vmware sd-wan vco firewall rules.

Note: 
Currently the 2 scripts provided only work with ACL used as outbound direction.
To be used with ACLs that are applied inbound src must be swapped with destination

Ex of some random Cisco config created to illustrated which lines can be converted
(this is not an real ACL used in production)

ip access-list extended ACL_NAME
  permit tcp any eq 80 88  10.20.210.30 0.0.0.1 eq 8443
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
  ip access-group ACL_NAME out

Gets converted to:
![Screenshot 2022-10-17 at 15 35 25](https://user-images.githubusercontent.com/76786046/196200617-57cd3c76-6cde-4bf4-8019-35db33976a9e.png)

