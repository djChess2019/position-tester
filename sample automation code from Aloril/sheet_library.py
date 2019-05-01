#!/usr/bin/env python3
import time
from datetime import datetime
from math import inf
from sheet_utils import *
import gspread.utils

UPDATE_INTERVAL = 120
VERSION_COL = 2
NET_ID_COL = 3
TOURNAMENT_ROW = 5
FIRST_ELO_ROW = 14
STATUS_FIRST_ELO_ROW = 6
STATUS_ROW_DIFF = FIRST_ELO_ROW - STATUS_FIRST_ELO_ROW
AUTO_PROCESS_LOG = "auto_process.log"
OPENINGS_PGN = "2moves_v1.pgn"
OPENINGS_PGN2 = "8moves_v3.pgn"
HARDCODE_INDEX = True #False not supported any more
ERROR_TIMEOUT = 25

def tournament2si(tournament):
    return ":".join(map(str_SI, tournament.split(":")))

SI2no = {_si:_no for _no, _si in SI}

def SI2no_str(s):
    global SI2no
    if s.startswith("depth"):
        return s
    if s[-1] in SI2no:
        return s[:-1] + str(SI2no[s[-1]])[1:]
    else:
        return s

def si2tournament(tournament):
    return ":".join(map(SI2no_str, tournament.split(":")))

def get_time_str():
    return time.strftime("%Y-%m-%dT%H_%M_%S", time.localtime(time.time()))

def get_UTC():
    return datetime.utcnow().isoformat()[:19] + " UTC"

def elo2sheet(elo):
    elo = float(elo)
    if -inf < elo < inf:
        return round(elo)
    else:
        return str(elo)

def log(msg):
    msg = get_time_str() + " " + msg
    with open(AUTO_PROCESS_LOG, "a") as fp_out:
        fp_out.write(msg + "\n")
    print(msg)

def add_row(sheet, wks, net_id):
    global status_ok_dict
    status_ok_set = set()
    cells = ['192x15', 'v0.10', int(net_id)]
    net_id = int(net_id)
    log("update status net_id to %s" % net_id)
    wks.update_cell(FIRST_ELO_ROW-1, NET_ID_COL, net_id)
    net_id -= 1
    log("add row with id%s\n" % (net_id,))
    #cells = ['192x15', 'v0.10', net_id] + ['']*26 + ['=IF(AC13<>"";IFERROR(N13-AC13;"");"")', '', '=if(AE13<>"";IFERROR(AE13-V13;"");"")']
    cells = ['192x15', 'v0.10', net_id]
    wks.insert_row(cells, FIRST_ELO_ROW)
    wks2 = sheet.worksheet("Status")
    wks2.insert_row(cells, STATUS_FIRST_ELO_ROW)
    
def edit_max(wks, id_lst, tour_lst):
    return
    for i in range(len(tour_lst)):
        tour = tour_lst[i]
        if tour.find(":")<0:
            continue
        cell = gspread.utils.rowcol_to_a1(TOURNAMENT_ROW-1, i+1)
        formula = '=MAX(%s:%s)' % (gspread.utils.rowcol_to_a1(FIRST_ELO_ROW, i+1),
                                   gspread.utils.rowcol_to_a1(len(id_lst)+1, i+1))
        wks.update_acell(cell, formula)

status_ok_set = set()
def check_status_sheet(sheet, cell):
    return
    global status_ok_dict
    #if cell in status_ok_set:
    #    return
    row, col = gspread.utils.a1_to_rowcol(cell)
    if row<=STATUS_ROW_DIFF: # or col>36:
        return
    wks2 = sheet.worksheet("Status")
    status_cell = gspread.utils.rowcol_to_a1(row-STATUS_ROW_DIFF, col)
    if HARDCODE_INDEX or wks2.acell(status_cell).value=="":
        wks2.update_acell(status_cell, "='Rating lists'!" + cell)
    status_ok_set.add(cell)
