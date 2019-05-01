#!/usr/bin/env python3
import sys, os, re, time, collections

def rename_old(filename):
    i = 0
    while True:
        filename2 = filename + ".old%i" % i
        if not os.path.exists(filename2):
            break
        i += 1
    os.rename(filename, filename2)

if __name__=="__main__":
    #SERVER = "testserver.lczero.org"
    SERVER = "ipv4.mooskagh.com:17346"
    #add to util.py too
    #TEST_SIZE = "20"
    #TEST_STR = "test%%ib%s-" % (TEST_SIZE,)
    #WEIGHT_PATTERN = "weights_" + TEST_STR + "%i.pb.gz"
    NETWORKS = SERVER + "/networks"
    last_downloaded = ""
    min_id = int(sys.argv[1])
    start_flag = True
    while True:
        found = False
        while not found:
            if os.path.exists(NETWORKS):
                line_lst = open(NETWORKS).readlines()
            else:
                line_lst = ['']
            game_count = collections.Counter()
            first_game_count = {}
            field_count = -1000
            current_net_id = ""
            value = previous_value = ""
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
                    if net_id < 37000: #test30, test35
                        TEST_NO = net_id//5000*5
                    elif net_id < 40000: #test37
                        TEST_NO = net_id//1000
                    else: #test40
                        TEST_NO = net_id//10000*10
                    m = re.match(r'.*href="(.*?)"', line)
                    i = line_lst.index(line)
                    blocks = re.match(r'.*<td>(.*?)</td>', line_lst[i+3]).group(1)
                    TEST_SIZE = blocks
                    TEST_STR = "test%%ib%s-" % (TEST_SIZE,)
                    WEIGHT_PATTERN = "weights_" + TEST_STR + "%i.pb.gz"
                    filename = WEIGHT_PATTERN % (TEST_NO, net_id)
                    tournament_args = {"20": ("256x20", "b20"), "10": ("128x10", "b10")}.get(TEST_SIZE)
                    if tournament_args and net_id>=min_id and not os.path.exists(filename):
                        #m = re.match(r'.*href="(.*?)".*?"(weights_.*?)"', line)
                        #print("TEST_SIZE:", TEST_SIZE, "blocks:", blocks)
                        #if blocks!=TEST_SIZE:
                        #    continue #for now skip this
                        #assert(blocks==TEST_SIZE)
                        weights_target = filename
                        weights_target2 = weights_target.replace(".pb.gz", ".txt.gz")
                        #weights_target3 = weights_target2.replace(".gz", "")
                        if TEST_NO>=35:
                            cmd = "wget http://%s%s -O %s && cp -iva %s ../networks/tmp/%s && mv -iv ../networks/tmp/%s ../networks/" % (SERVER, m.group(1), weights_target, weights_target, weights_target, weights_target)
                        else:
                            cmd = "wget http://%s%s -O %s && /usr/local/src/lczero-training_git/tf/net.py -i %s -o ../networks/tmp/%s && mv -iv ../networks/tmp/%s ../networks/" % (SERVER, m.group(1), weights_target, weights_target, weights_target2, weights_target2)
                        print(cmd)
                        os.system(cmd)
                        last_downloaded = weights_target
                        #for size, size_id in (("128x10", "b10"), ("64x6", "b6")):
                        #for size, size_id in (("64x6", "b6"),):
                        #for size, size_id in (("256x20", "b20"),):
                        for size, size_id in (tournament_args,):
                            old_net_id_s = "test%s%s-%i" % (TEST_NO, size_id, net_id-1)
                            net_id_s = "test%s%s-%i" % (TEST_NO, size_id, net_id)
                            #os.system("cd SF9; ./sheet/add_row.py %s 10 %s %s; cd .." % (size, net_id_s, old_net_id_s))
                            print("cd SF9; ./add_tournaments.py --test %s %s; cd .." % (TEST_NO, net_id_s))
                            os.system("cd SF9; ./add_tournaments.py --test %s %s; cd .." % (TEST_NO, net_id_s))
                            os.system("cd SF9; ./sheet/write_msg.py %s 1:1k queued" % (net_id_s,))
                            #os.system('./sheet/write_msg.py %s 1:100 downloading&' % net_id)
                            #os.system(cmd)
                            #os.system("cd SF9; ./add_tournaments.py %s; cd .." % net_id)
                            #os.system('./sheet/write_msg.py %s 1:1000 "once current match finishes"' % net_id)
                            #os.system('./sheet/write_msg.py %s 1:100 "download done"' % net_id)
                        found = True
                        break
                elif field_count==2 and int(current_net_id)>=30000 and TEST_NO not in (35, 37):
                    if TEST_NO not in first_game_count:
                        first_game_count[TEST_NO] = int(value)
                    game_count[TEST_NO] += int(value)
            else:
                if last_downloaded:
                    print("last_downloaded:", last_downloaded, end=" ")
                for no in sorted(game_count.keys()):
                    print("test:", no, "game_count:", game_count[no], "first_game_count:", first_game_count[no], end=" ")
                print()
                if start_flag:
                    start_flag = False
                else:
                    time.sleep(60)
                if os.path.exists(NETWORKS):
                    rename_old(NETWORKS)
                os.system("wget http://%s/networks -O %s" % (SERVER, NETWORKS))
        print("waiting for next net")
        
