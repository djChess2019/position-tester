#!/usr/bin/env python3
import gspread, gspread.utils
import re, time, string, sys, traceback
from oauth2client.service_account import ServiceAccountCredentials
import os.path
this_dir = os.path.split(__file__)[0]
if this_dir not in sys.path:
    sys.path.append(this_dir)
from elo import Elo
from sheet_library import *

STATUS_CELL = "J1" #also J2, P1, P2 and W1
LCZERO = "lczero"

def latest_tournament(tournament_log = "tournament.log", engine=LCZERO):
    for line in open(tournament_log):
        l = line.split()
        if len(l) < 3:
            return None
        if l[1].startswith(engine):
            eng1 = l[1].split(":")
            eng2 = l[2].split(":")
            nodes1 = eng1[-1]
            nodes2 = eng2[-1]
            net_id = eng1[0].split("_")[-1]
            t1, t2 = nodes1, nodes2
            if eng1[1]=="depth":
                t1 = "depth" + t1
            if eng2[1]=="depth":
                t2 = "depth" + t2
            tournament = t1 + ":" + t2
        elif l[1].startswith("./cutechess-cli"):
            log_file = l[-1]
    if engine=="lczero" and not re.match(r"lc0.*_id%s_[dn]%s_.*[dn]%s_" % (net_id, nodes1, nodes2), log_file):
        return None
    if not os.path.exists(log_file):
        return None
    if os.path.exists(log_file + ".bz2"):
        return None
    return net_id, tournament, log_file

status_wks = None
def robust_update(cell, desc, value):
    global status_wks, wks_name, sheet_name
    log("%s update %s: %s" % (desc, cell, value))
    error_timeout = ERROR_TIMEOUT
    error_status = False
    had_error = False
    while True:
        try:
            if error_status:
                status_wks = None
                get_sheet(sheet_name)
                if cell!=STATUS_CELL:
                    sheet.worksheet(wks_name)
                error_status = False
            if not status_wks:
                status_wks = sheet.sheet1
            if cell==STATUS_CELL:
                status_wks.update_acell(cell, value)
            else:
                wks.update_acell(cell, value)
            break
        except:
            error_status = had_error = True
            e = sys.exc_info()[0]
            log("Exception %s when updating cell %s with %s, sleeping %s" % (e, cell, value, error_timeout))
            traceback.print_exc()
            time.sleep(error_timeout)
            error_timeout *= 2
        if error_timeout>=200:
            print("Does not work for some reason, exit!!")
            exit(1)
    if had_error:
        print("Retry succeeded!")

def update(cell, desc, value, version=None):
    robust_update(cell, desc, value)
    return cell

def update_status(desc, value):
    robust_update(STATUS_CELL, desc, value)

def monitor_log(cell, desc, log_file, version, elo_update=True):
    global wks
    t0 = time.time()
    next_update = time.time() + UPDATE_INTERVAL
    m = re.match(r".*_g(\d+).log", log_file)
    if m:
        game_count = int(m.group(1))
    elif log_file.endswith("_gall.log"):
        game_count = len(open(OPENINGS_PGN).read().split("\n\n"))//2*2
    elif log_file.endswith("_gall8.log"):
        game_count = len(open(OPENINGS_PGN2).read().split("\n\n"))//2*2
    else:
        game_count = 1000
    if elo_update:
        cell = update(cell, desc, "est. in %is" % UPDATE_INTERVAL, version)
    update_status(desc, "%s, progress update in %is or after 1. game" % (desc, UPDATE_INTERVAL))
    pos = 0
    fp = open(log_file)
    while True:
        fp.seek(pos)
        line = fp.readline()
        if not line:
            fp.close()
            time.sleep(0.1)
            fp = open(log_file)
            continue
        pos = fp.tell()
        if line.startswith("Score of"):
            score_line = line
            if time.time() >= next_update:
                if time.time() > t0 + 1200:
                    log("relogin")
                    wks = find_wks(net_id)
                    t0 = time.time()
                m = re.match(r".*: (.*?)  (\[.*)", line)
                if m:
                    wld = m.group(1)
                    w, l, d = map(int, wld.split("-"))
                    e = Elo(w, l, d)
                    if elo_update:
                        cell = update(cell, desc, "%.2f\n+-%.2f\nhi:%.2f\nlo:%.2f" % (e.diff(), e.errorMargin(), e.diff()+e.errorMargin(), e.diff()-e.errorMargin()), version)
                    status_elo_str = " %.2f+-%.2f" % (e.diff(), e.errorMargin())
                    update_status(desc, "%s %s %s/%s%s" % (desc, wld, m.group(2), game_count, status_elo_str))
                    next_update = time.time() + UPDATE_INTERVAL
        elif line.startswith("Elo difference"):
            elo_line = line
            m = re.match(r".*: (.*) \+/- (.*)", line)
            elo_str, error = m.groups()
            break
    fp.close()
    if elo_update:
        #if error.startswith("nan"):
        #    cell = update(cell, desc, "error bar nan", version)
        #else:
        #    cell = update(cell, desc, round(float(elo)), version)
        elo = elo2sheet(elo_str)
        cell = update(cell, desc, elo, version)
    update_status(desc, "done %s %s+-%s" % (desc, elo_str, error))
    with open(AUTO_PROCESS_LOG, "a") as fp_out:
        fp_out.write(score_line)
        fp_out.write(elo_line)
        fp_out.write("\n")

def find_version_and_net_id(wks, version, net_id, id_lst, tournament):
    if net_id in id_lst:
        row = id_lst.index(net_id) + 1
        #if not tournament.find("depth")>=0 and id_lst[row]==net_id: #next one is same id too? search with version too
        if id_lst[row]==net_id: #next one is same id too? search with version too
            version_lst = wks.col_values(VERSION_COL)
            combined_lst = ["%s_%s" % (version_lst[i], id_lst[i]) for i in range(min(len(version_lst), len(id_lst)))]
            row = combined_lst.index("v0.%s_%s" % (version, net_id)) + 1
        return row
    else:
        return None

net_id2tab = {}
tab2id_lst = {}
def read_net_id_index():
    global net_id2tab, tab2id_lst
    for line in open("sheet/net_index/net_tabs.txt"):
        filename, tabname = line.strip().split(":")
        l = []
        for line2 in open("sheet/net_index/" + filename):
            net_id = line2.strip()
            l.append(net_id)
            net_id2tab[net_id] = tabname
        tab2id_lst[tabname] = l

def get_net_id2tab():
    global net_id2tab
    if not net_id2tab:
        read_net_id_index()
    return net_id2tab

def get_tab2id_lst():
    global tab2id_lst
    if not tab2id_lst:
        read_net_id_index()
    return tab2id_lst

def net_id2id_lst(net_id):
    return get_tab2id_lst()[get_net_id2tab()[net_id]]

wks_name = None
def find_wks(net_id):
    global wks_name
    n2t = get_net_id2tab()
    if net_id in n2t:
        wks_name = n2t[net_id]
        return sheet.worksheet(wks_name)
    else:
        wks_name = None
        return None
        
def find_cell(wks, net_id, tournament, version=None):
    if version and version.endswith("v"):
        version = version[:-1]
    tournament = tournament2si(tournament)
    if HARDCODE_INDEX:
        id_lst = net_id2id_lst(net_id)
        tour_lst = open("sheet/net_index/tournaments.lst").read().split("\t")
    else:
        id_lst = wks.col_values(NET_ID_COL)
        tour_lst = wks.row_values(TOURNAMENT_ROW)
    row = col = 0
    if tournament in tour_lst:
        col = tour_lst.index(tournament) + 1
    else:
        raise ValueError("tournament %s not found" % (tournament,))
    row = find_version_and_net_id(wks, version, net_id, id_lst, tournament)
    if not row:
        add_row(sheet, wks, net_id)
        row = FIRST_ELO_ROW
        edit_max(wks, id_lst, tour_lst)
    return gspread.utils.rowcol_to_a1(row, col)

sheet_name = None
def get_sheet(name="Leela Chess Zero vs Stockfish 9"):
    global sheet_name
    credentials_file = os.path.split(__file__)[0] + os.sep + "credentials.json"
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(credentials)
    sheet_name = name
    return gc.open(name)

def set_wks(wks_arg):
    global wks
    wks = wks_arg

def set_sheet(sheet_arg):
    global sheet
    sheet = sheet_arg

if __name__=="__main__":
    if len(sys.argv) > 1:
        STATUS_CELL = sys.argv[1]
    if len(sys.argv) > 2:
        engine = sys.argv[2]
    else:
        engine = LCZERO
    print("Status cell:", STATUS_CELL)
    done_set = set()
    while True:
        result = latest_tournament(engine=engine)
        if not result:
            time.sleep(10)
            continue
        net_id, tournament, log_file = result
        version = log_file.split("_")[1]
        key = net_id, tournament, version
        if key in done_set:
            time.sleep(1)
            continue
        done_set.add(key)
        sheet = get_sheet()
        wks = find_wks(net_id)
        if engine==LCZERO:
            cell = find_cell(wks, net_id, tournament, version)
            tournament = tournament2si(tournament)
            monitor_log(cell, "id%s %s" % (net_id, tournament), log_file, version)
        else:
            monitor_log(None, "%s %s" % (engine, tournament), log_file, engine, elo_update=False)
