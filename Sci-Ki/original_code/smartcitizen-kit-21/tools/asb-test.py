import sck
import yaml
import json
import os
import sys
import traceback
from pathlib import Path

do_test = False

def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def oneLine(msg):
    enablePrint()
    sys.stdout.write(msg)
    sys.stdout.flush()
    if not verbose: blockPrint()

def enablePrint():
    sys.stdout = sys.__stdout__

# Smart Citizen Kit
kit = sck.sck()
kit.begin(get_sensors=True)
try:
    sensors_enabled = kit.sensor_enabled
    do_test = True
except:
    print('There are no enabled sensors')

verbose = False
blockPrint()
if '-v' in sys.argv:
    verbose = True
    enablePrint()

if '-h' in sys.argv:
    print ('Help coming - TODO')

# Data files
if do_test:

    # Sensor ID given manually by running this script
    # for example: python3 test.py 001292129
    if '--kit_id' not in sys.argv:
        do_test = False
        print('An ID must be provided')
    else :
        kit_id = sys.argv[sys.argv.index('--kit_id')+1]
        print('Kit ID: ' + str(kit_id))

    update_cal = True
    if '--dry_run' in sys.argv: update_cal = False

    if 'DATA_PATH' in os.environ: folder_data = os.environ['DATA_PATH']
    else: print ('DATA_PATH variable not defined in environment'); exit()

    # folder_data = Path('../smartcitizen-data/')
    file_hardware = os.path.join(folder_data,f'hardware/{kit_id}.json')
    file_calibrations = os.path.join(folder_data, 'calibrations/calibrations.json')
    try:
        with open(file_hardware, 'r') as file:
            data_hardware = json.load(file)
    except:
        print('Hardware file not found. Expected location: ' + str(file_hardware))
        do_test = False
    try:
        with open(file_calibrations, 'r') as file:
            data_calibrations = json.load(file)
    except:
        print('Calibrations file not found. Expected location: ' +
              str(file_calibrations))
        do_test = False

if do_test:

    # Sensors basics
    this_sensor = 'ADS1x15 ADC'
    these_sensors = []
    this_kit = {}
    for sensor in sensors_enabled:
        if this_sensor in sensor:
            these_sensors.append(sensor)
    # Getting metrics
    these_sensors_metrics = kit.readSensors(
        sensors=these_sensors, iter_num=2, delay=0.1, unit='V', method='avg')

    # Kit update
    this_kit[kit_id] = these_sensors_metrics

    # Text formatting (Ch0)
    new_keys = []
    for item in this_kit[kit_id]:
        item_formatted = item[-8:]
        new_keys.append(item_formatted)
    this_kit_formatted = {}
    this_kit_formatted[kit_id] = dict(
        zip(new_keys, list(this_kit[kit_id].values())))

    # From V to mV, rounded
    for item in this_kit_formatted[kit_id]:
        this_kit_formatted[kit_id][item] = round(
            this_kit_formatted[kit_id][item] * 1000, 2)

    # Getting ID's from hardware.json
    hardware_ids = data_hardware['1']['ids']

    # Getting values from calibrations.yaml and update it
    calibrations_values = {}
    data_index = 0
    for i in hardware_ids.keys():
        try:
            wen = f"0x{i.strip('AS_')[:i.index('_')]} Ch{i.strip('AS_')[i.index('_')+1]}"
            aen = f"0x{i.strip('AS_')[:i.index('_')]} Ch{i.strip('AS_')[i.index('_')+2]}"

            calibrations_values[hardware_ids[i]] = data_calibrations[hardware_ids[i]]

        except KeyError:
            print('Sensor #' + str(hardware_ids[i]) + ' does not exist in ' +
                  str(file_calibrations))
        except:
            print ('Unknow error occurred')
            exit()
        else:
            calibrations_values[hardware_ids[i]]['we_electronic_zero_mv'] = str(this_kit_formatted[kit_id][wen])
            calibrations_values[hardware_ids[i]]['ae_electronic_zero_mv'] = str(this_kit_formatted[kit_id][aen])


    # Update the calibrations file
    print ('Collected calibration values')
    if update_cal:
        for item in calibrations_values:
            print (item)
            for value in calibrations_values[item]:
                print (f'\t{value}: {calibrations_values[item][value]}')
        print ('----------------')

        while True:
            what_to_do = input('Like what you see? [y/n]: ')
            if what_to_do == 'y' or what_to_do == 'n':
                break
            else:
                print ('Please input [y/n]')

        if what_to_do == 'y':
            data_calibrations.update(calibrations_values)
            with open(file_calibrations, 'w') as file:
                json.dump(data_calibrations, file, indent=2)
            print('Calibrations file updated (' + str(file_calibrations) + ')')
        else:
            print ('Nothing updated. Thank you for nothing sir')
    else:
        for item in calibrations_values:
            print (item)
            for value in calibrations_values[item]:
                print (f'\t{value}: {calibrations_values[item][value]}')
        print ('----------------')