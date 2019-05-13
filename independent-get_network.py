#!/usr/bin/env python3
import sys, os, re, time, collections
# simply enter the min_id and max_id below
# currently only logic for min_id is present.
if __name__=="__main__":
    #SERVER = "testserver.lczero.org"
    SERVER = "ipv4.mooskagh.com:17346"
    #add to util.py too
    #TEST_SIZE = "20"
    #TEST_STR = "test%%ib%s-" % (TEST_SIZE,)
    #WEIGHT_PATTERN = "weights_" + TEST_STR + "%i.pb.gz"
    NetworksHtm =  "networks.htm"
    NetworksDir = "../lc0nets/"
    last_downloaded = ""
    min_id = 20000
    max_id = 30000
    field_count = 0
    previous_value2 = ""
    previous_value = ""
    value = ""
    os.system("wget http://%s/networks -O %s" % (SERVER, NetworksHtm))
    line_lst = open(NetworksHtm).readlines()
    existingNets = os.listdir(NetworksDir)
    for line in line_lst:
        m = re.match(r".*<td>(.*?)</td>", line)
        if not m:
            continue
        field_count += 1
        previous_value2 = previous_value
        previous_value = value
        value = m.group(1)
        if value.find("get_network?sha")>0:
            field_count = 0
            net_hash_flag = 1
            current_net_id = previous_value2
            net_id = int(current_net_id)
            if net_id > max_id:
                continue
            if net_id <= min_id:
                break
            if net_id%25 != 0:
                continue
            if net_id < 37000: #test30, test35
                TEST_NO = net_id//5000*5
            elif net_id < 40000: #test37
                TEST_NO = net_id//1000
            else: #test40
                TEST_NO = net_id//10000*10
            m = re.match(r'.*href="(.*?)"', line)
            i = line_lst.index(line)
            weights_target = "%i" % (net_id)
            if os.path.isfile(NetworksDir + weights_target):
                continue
            cmd = "wget http://%s%s -O %s%s" % (SERVER, m.group(1), NetworksDir, weights_target)
            print(cmd)
            os.system(cmd)


        
