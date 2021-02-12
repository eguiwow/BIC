#!/usr/bin/python

from traceback import print_exc
import sys, time, os
from backup import *
import shutil

sys.path.append("./tools")

def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def oneLine(msg):
    enablePrint()
    sys.stdout.write(msg)
    sys.stdout.flush()
    if not verbose: blockPrint()

def enablePrint():
    sys.stdout = sys.__stdout__

if '-h' in sys.argv or '--help' in sys.argv or '-help' in sys.argv:
    print('USAGE:\n\nresgister.py [options] action[s]')
    print('\noptions: -v: verbose; -t: test device')
    print('actions: register, inventory')
    print('register options: -n platform_name -i kit_blueprint_id (default: 26)')
    print('inventory -d "description" --with-test [y/n] (default: n)')
    sys.exit()

import sck
kit = sck.sck(to_register = True)
kit.begin() 

verbose = False
blockPrint()
if '-v' in sys.argv: 
    verbose = True
    enablePrint()

if 'register' in sys.argv:
    kit.getInfo()

    if '-n' not in sys.argv:
        kit.platform_name = 'test #' 
    else:
        kit.platform_name = sys.argv[sys.argv.index('-n')+1]

    if '-i' in sys.argv:
        try:
            bid = int(sys.argv[sys.argv.index('-i')+1])
        except:
            enablePrint()
            print('Failed parsing blueprint ID, please try again.')
            sys.exit()
        kit.blueprint_id = bid

    if '-t' in sys.argv:
        print ('Setting test device')
        kit.is_test = True

    kit.platform_name = kit.platform_name + ' #' + kit.esp_macAddress[-5:].replace(':', '')
    kit.register()

    enablePrint()
    print("\r\nSerial number: " + kit.sam_serialNum)
    print("Mac address: " + kit.esp_macAddress)
    print("Device token: " + kit.token)
    print("Platform kit name: " + kit.platform_name)
    print("Platform page:" + kit.platform_url)

if 'inventory' in sys.argv:
    try:
        from secret import inventory_path
    except:
        print ('No inventory path defined, using inventory/ folder')
        inventory_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'inventory')
        pass

    print (f'Using inventory in: {inventory_path}')
    kit.description = sys.argv[sys.argv.index('-d')+1]
    kit.getInfo()

    if '--with-test' in sys.argv: tested = 'y'
    else: tested = 'n'

    if not hasattr(kit, 'token'):
        kit.token = ''
    if not hasattr(kit, 'platform_name'):
        kit.platform_name = ''
    if not hasattr(kit, 'platform_url'):
        kit.platform_url = ''

    local_inv_path = os.path.join(inventory_path, 'deliveries')
    s3_inv_path = "inventory/deliveries"
    local_inv_name = "inventory.csv"
    if not os.path.exists(local_inv_path): os.makedirs(local_inv_path)

    try:
        # Try to download file from S3
        sync = S3handler()
        sync.download(os.path.join(local_inv_path, local_inv_name), os.path.join(s3_inv_path, local_inv_name))
    except:
        # Keep things local
        print_exc()
        print('Problem downloading file from S3, using local file')

        if os.path.exists(os.path.join(local_inv_path, local_inv_name)):
            shutil.copyfile(os.path.join(local_inv_path, local_inv_name), local_inv_path+".BAK")
            csvFile = open(os.path.join(local_inv_path, local_inv_name), "a")
        else:
            csvFile = open(os.path.join(local_inv_path, local_inv_name), "w")
            csvFile.write("time,serial,mac,sam_firmVer,esp_firmVer,description,token,platform_name,platform_url,tested,validated,min_validation_date,max_validation_date,replacement,test,destination,batch\n")
        pass
    else:
        # Open the file 
        print ('File from S3 synced correctly')
        csvFile = open(os.path.join(local_inv_path, local_inv_name), "a")

    csvFile.write(time.strftime("%Y-%m-%dT%H:%M:%SZ,", time.gmtime()))
    csvFile.write(kit.sam_serialNum + ',' + kit.esp_macAddress + ',' + kit.sam_firmVer + ',' + kit.esp_firmVer + ',' + kit.description + ',' + kit.token + ',' + kit.platform_name + ',' + kit.platform_url + ',' + tested + ',' + ',' + ',' +',' + ',' +',' + ',' +'\n')
    csvFile.close()

    # Put the file in S3
    sync = S3handler()
    resp = sync.upload(os.path.join(local_inv_path, local_inv_name), os.path.join(s3_inv_path, local_inv_name))

    if resp is None: print ('No response, review bucket')
    else: print ('Success!')