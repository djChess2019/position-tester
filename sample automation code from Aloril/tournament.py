#!/usr/bin/env python3
import os, sys, time, glob, argparse, re
sys.path.append("sheet")
from sheet_utils import str_SI
CONCURRENCY = 10
CONCURRENCY10k = 20
LC0_CONCURRENCY = 2
LC0_CONCURRENCY10k = 8

VERBOSE_STATS = True

BREAK_FLAG = "break.flag"
TOURNAMENT_LOG = "tournament.log"

pause_cells = []
pause_flag = False

def get_tb_option(version):
    if version.endswith("tb"):
        tb_option = 'option.SyzygyPath=/usr/games/syzygy'
        if version.endswith("ndtb"):
            tb_option += ' option.SyzygyDraw=false'
    elif version[:-1].endswith("tb"):
        tb_option = 'option.SyzygyPath=/usr/games/syzygy' + version[-1]
    elif version[:-1].endswith("tb7p"):
        tb_option = 'option.SyzygyPath=%s/test/syzygy7p%s' % (os.getcwd(), version[-1])
    elif version.endswith("tb6r"):
        tb_option = 'option.SyzygyPath=%s/test/syzygy6r' % (os.getcwd(),)
    elif version.endswith("tb6p3"):
        tb_option = 'option.SyzygyPath=%s/test/syzygy6p3' % (os.getcwd(),)
    else:
        tb_option = ''
    return tb_option

def build_args(arg, quiet_flag=False):
    name, stype, count = arg.split(":")
    if name.startswith("lczero"):
        try:
            lczero, net_id = name.split("_")
        except:
            print(name)
            raise
        if net_id.endswith("pb"):
            weights = "networks/download/test_run/weights_%s.pb.gz" % net_id[:-2]
        else:
            weights = "networks/weights_%s.txt" % net_id
        if not os.path.exists(weights):
            weights2 = "networks/weights_%s.txt.gz" % net_id
            if not os.path.exists(weights2):
                weights3 = "networks/weights_%s.pb.gz" % net_id
                if not os.path.exists(weights3):
                    if not quiet_flag:
                        print("%s, %s and %s does not exists" % (weights, weights2, weights3))
                    return None, None, None
                weights2 = weights3
            weights = weights2
        lc0_version = lczero[6:]
        lc0_version_no = int(re.match(r"(\d+)", lc0_version).group(1))
        if lc0_version_no <= 2:
            visits_arg = 'arg="--playouts=%s"' % count
        elif lc0_version_no <= 10:
            visits_arg = 'arg="--visits=%s"' % count
        else:
            visits_arg='' #arg="--minibatch-size=1"'
        if lc0_version_no <= 10:
            tc = ""
            debug_option = ''
        else:
            tc = "nodes=%s" % count
            if lc0_version_no <= 16:
                debug_option = 'option."Display verbose move stats"=true'
            else:
                debug_option = 'option."VerboseMoveStats"=true'
            if not VERBOSE_STATS:
                debug_option = ''
        if lc0_version in ("2", "1", "4", "5"):
            noponder = 'arg="--noponder"'
        else:
            noponder = ''
        if lc0_version_no==16 and "v" in lc0_version:
            depth1_arg = 'arg="--depth-one-value-mode"'
            tc = "nodes=1000"
        elif lc0_version_no in (20, 201) and "v" in lc0_version:
            depth1_arg = '' #'arg="--max-collision-events=1" arg="--max-collision-visits=1" arg="--no-out-of-order-eval"'
            tc = "nodes=1000"
        else:
            depth1_arg = ""
        m = re.match(r".*\dsb(\d+)$", lc0_version) #server
        if m:
            batchsize = 'option."MinibatchSize"=%s' % (m.group(1),)
        else:
            m = re.match(r".*\db(\d+)$", lc0_version)
            if m:
                batchsize = 'arg="--minibatch-size=%s"' % (m.group(1),)
            else:
                batchsize = ''
        tb_option = get_tb_option(lc0_version)
        return '-engine name="LCZero 0.%s id%s %s%s" cmd=./%s.sh arg="--weights=%s/%s" arg="--threads=1" %s %s %s %s proto=uci %s %s st=1000000 %s' % (lc0_version, net_id, stype[0], count, lczero, os.getcwd(), weights, visits_arg, noponder, depth1_arg, batchsize, debug_option, tb_option, tc), "lc0_%s_id%s_%s%s" % (lc0_version, net_id, stype[0], count), count
    else:
        if int(count) > 1000000 or (int(count) > 15 and stype=="depth"):
            hash_size = 1024
        else:
            hash_size = 128
        if name.startswith("sf"):
            version=name[2:]
            tb_option = get_tb_option(version)
            return '-engine name="Stockfish %s %s%s" cmd=./stockfish%s proto=uci option."Move Overhead"=100 option.Hash=%i %s st=1000000 %s=%s' % (version, stype[0], count, version, hash_size, tb_option, stype, count), "sf" + version + "_" + stype[0] + count, count
        else: #cfish
            name, version = name.split("_")
            tb_option = get_tb_option(version)
            return '-engine name="Cfish %s %s%s" cmd=./cfish_170618 proto=uci option."Move Overhead"=100 option.Hash=%i %s st=1000000 %s=%s' % (version, stype[0], count, hash_size, tb_option, stype, count), name + "_" + version + "_" + stype[0] + count, count
        #return '-engine name="Stockfish 9 %s%s" cmd=./stockfish9 proto=uci option.SyzygyPath=/usr/games/syzygy option."Move Overhead"=100 option.Hash=128 st=1000000 %s=%s' % (stype[0], count, stype, count), "sf9_" + stype[0] + count, count
        #return '-engine name="Stockfish 9 %s%s" cmd=./stockfish9 proto=uci option."Move Overhead"=100 st=1000000 %s=%s' % (stype[0], count, stype, count), "sf9_" + stype[0] + count, count

def get_time_str():
    return time.strftime("%Y-%m-%dT%H_%M_%S", time.localtime(time.time()))

def get_net_id_tournament(args1, args2):
    al1 = args1.split(":")
    al2 = args2.split(":")
    t = al1[0].split("-")
    if len(t)<2:
        return None, None
    net_id = int(t[-1])
    if al1[1]=="nodes": t1 = ""
    else: t1 = al1[1]
    t1 += al1[2]
    if al2[1]=="nodes": t2 = ""
    else: t2 = al2[1]
    t2 += al2[2]
    tournament_name = str_SI(t1)+":"+str_SI(t2)
    return net_id, tournament_name

def score_tournament(conditionals, *args):
    engine1, out1, count1 = build_args(args[0], quiet_flag=True)
    engine2, out2, count2 = build_args(args[1], quiet_flag=True)
    if not engine1 or not engine2:
        return False
    games = args[2]
    out = "%s_%s_g%s" % (out1, out2, games)
    if os.path.exists(out + ".pgn") or os.path.exists(out + ".pgn.bz2"):
        return False
    netid, tour = get_net_id_tournament(args[0], args[1])
    if netid:
        for i in range(len(conditionals)):
            score, cond = conditionals[i][:2]
            if eval(cond):
                conditionals[i][2] += 1
                return score
    return True

def sort_tournaments(matches):
    conditionals = []
    lst = []
    base_score = 10**6-1
    for match in matches:
        if match.startswith("cond "):
            conditionals.append([base_score, match[5:], 0])
        else:
            score = score_tournament(conditionals, *match.split())
            if score:
                if score==True:
                    score = base_score * 10**6
                else:
                    score = score * 10**6 + base_score
                lst.append((score, match))
        base_score -= 1
    lst.sort()
    lst.reverse()
    return lst, conditionals

def tournament(*args):
    global pause_flag
    if len(args)==0:
        handle_pause_cells("continue")
        sys.exit(0)
    st = get_time_str()
    engine1, out1, count1 = build_args(args[0])
    engine2, out2, count2 = build_args(args[1])
    if not engine1 or not engine2:
        return False
    games = args[2]
    out = "%s_%s_g%s" % (out1, out2, games)
    if os.path.exists(out + ".pgn") or os.path.exists(out + ".pgn.bz2"):
        if not quiet_existing:
            print("%s.pgn or %s.pgn.bz2 already exists, skipping" % (out, out))
        return False
    print(st + " " + " ".join(args))
    #if "--depth-one-value-mode" in engine1: #Lc0 v0.16 PR72 for value head
    if (int(count2)/int(count1) >= 10000 and not out1.endswith("_d1")) or args[0][:3]==args[1][:3]=="sf9" or (int(count1)<=10 and not out1.endswith("_d1")):
        if "Display verbose move stats" in engine1: #Lc0 v0.16
            concurrency = min(LC0_CONCURRENCY10k, CONCURRENCY10k)
        else:
            concurrency = CONCURRENCY10k
    else:
        if "Display verbose move stats" in engine1: #Lc0 v0.16
            concurrency = min(LC0_CONCURRENCY, CONCURRENCY)
        else:
            concurrency = CONCURRENCY

    #if games=="all_test":
    #    input_pgn = "test.pgn"
    if games.startswith("all"):
        if games.find("_")>0:
            input_pgn = games.split("_")[1] + ".pgn"
        elif games[-1]=="8":
            input_pgn = "8moves_v3.pgn"
        else:
            input_pgn = "2moves_v1.pgn"
        games_no = len(open(input_pgn, "rb").read().decode("latin-1").replace("\r\n", "\n").split("\n\n"))//2*2
        cmd = "./cutechess-cli -concurrency %i -debug -recover %s %s -games %s -pgnout %s.pgn -openings file=%s -repeat 2 > %s.log" % (concurrency, engine1, engine2, games_no, out, input_pgn, out)
    else:
        cmd = "./cutechess-cli -concurrency %i -debug -recover %s %s -games %s -pgnout %s.pgn -srand 42 -openings file=2moves_v1.pgn order=random > %s.log" % (concurrency, engine1, engine2, games, out, out)
    with open(TOURNAMENT_LOG, "a") as fp:
        fp.write(st + " " + " ".join(args) + "\n")
        fp.write(st + " " + cmd + "\n")
    for filename in glob.glob("/tmp/reserve*.flag"):
        os.remove(filename)
    if not pause_flag:
        handle_pause_cells("pause")
        pause_flag = True
    m = re.match(r'.*arg="--weights=(.*?)"', cmd)
    if m:
        weights = m.group(1)
        print("prereading", weights)
        open(weights, "rb").read() #cache by OS
        print(".. done")
    os.system(cmd)
    if open(out + ".pgn").read().find("abandoned")>=0:
        msg = st + " has abandoned games: " + out + ".pgn"
        print()
        print("!"*60)
        print(msg)
        print("!"*60)
        print()
        with open(TOURNAMENT_LOG, "a") as fp:
            fp.write(msg + "\n")
    else:
        os.system("time bzip2 -9v %s.log %s.pgn&" % (out, out))
    return True

def handle_pause_cells(cmd):
    if pause_cells:
        if cmd=="pause":
            os.system("killall -STOP cutechess-cli")
        else:
            os.system("killall -CONT cutechess-cli")
        for pause in pause_cells:
            os.system("%s %s&" % (pause, cmd))

if __name__=="__main__":
    if os.path.exists(BREAK_FLAG):
        sys.exit(1)
    parser = argparse.ArgumentParser(description="Run tournament according to arguments or tournament.lst")
    parser.add_argument('tournament', nargs='*', help="tournament to run")
    parser.add_argument('-l', '--loop', help="loop reading tournament.lst", action='store_const', const=True, default=False)
    parser.add_argument('-1', '--conc1', help="Concurrency, default %i" % CONCURRENCY, type=int, default=CONCURRENCY)
    parser.add_argument('-2', '--conc2', help="Concurrency for 10kx, default %i" % CONCURRENCY10k, type=int, default=CONCURRENCY10k)
    parser.add_argument('--lc0_conc1', help="Concurrency, default %i" % LC0_CONCURRENCY, type=int, default=LC0_CONCURRENCY)
    parser.add_argument('--lc0_conc2', help="Concurrency for 10kx, default %i" % LC0_CONCURRENCY10k, type=int, default=LC0_CONCURRENCY10k)
    parser.add_argument('-p', '--pause_cells', nargs='*', help="Scripts to run when pausing other tournaments", default=[])
    parser.add_argument('-q', '--quiet_existing', help="Silently skip done tournaments", action='store_const', const=True, default=False)
    parser.add_argument('--list_tournaments', help="List available tournament", action='store_const', const=True, default=False)
    parser.add_argument('-n', '--no_verbose_stats', help="Verbose stats by Lc0 in log", action='store_const', const=True, default=not VERBOSE_STATS)
    args = parser.parse_args()
    print("tournament:", args.tournament)
    print("loop:", args.loop)
    print("conc1:", args.conc1)
    print("conc2:", args.conc2)
    print("pause_cells:", args.pause_cells)
    print("quiet_existing:", args.quiet_existing)
    print("no_verbose_stats:", args.no_verbose_stats)
    pause_cells = args.pause_cells
    quiet_existing = args.quiet_existing
    CONCURRENCY = args.conc1
    CONCURRENCY10k = args.conc2
    LC0_CONCURRENCY = args.lc0_conc1
    LC0_CONCURRENCY10k = args.lc0_conc2
    VERBOSE_STATS = not args.no_verbose_stats
    if args.loop or args.list_tournaments:
        while not os.path.exists(BREAK_FLAG):
            matches = open("tournament.lst").readlines()
            if not matches[0].strip():
                tournament()
            matches2, conditionals2 = sort_tournaments(matches)
            if args.list_tournaments:
                total_count = 0
                for score, cond, count in conditionals2:
                    total_count += count
                    print(count, cond.strip())
                print("total count:", total_count)
                print("-"*60)
                for match in matches2:
                    print(match)
                sys.exit(0)
            for match in [m for _, m in matches2]:
                if tournament(*match.split()):
                    break
            else:
                if pause_flag:
                    handle_pause_cells("continue")
                    pause_flag = False
                    print("all done, sleeping")
                time.sleep(5)
    else:
        tournament(*args.tournament)
