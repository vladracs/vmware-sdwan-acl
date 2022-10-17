# vmware-sdwan-acl

python script that reads a cisco config file using the cisco-acl "library", and uses the result dictionary to build vmware sd-wan vco firewall rules.

Note: 
Currently the 2 scripts provided only work with ACL used as outbound direction.
To be used with ACLs that are applied inbound src must be swapped with destination

Ex of some random Cisco config created to illustrated which lines can be converted
(this is not an real ACL used in production)

![Screenshot 2022-10-17 at 16 16 23](https://user-images.githubusercontent.com/76786046/196200949-fd439ee0-639f-40cf-a3cd-f118d891263e.png)

Gets converted to:
![Screenshot 2022-10-17 at 15 35 25](https://user-images.githubusercontent.com/76786046/196200617-57cd3c76-6cde-4bf4-8019-35db33976a9e.png)

