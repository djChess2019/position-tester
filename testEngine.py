from typing import List, Any
import sys
import os
import numpy as np
import chess
import chess.engine
import json
import datetime
from datetime import timedelta
#    'F:/leela/lc0-v0.20.2-t40B/lc0.exe --weights=F:/leela/nets/32880 --history-fill=always --cpuct=3.0 --minibatch-size=512 --move-overhead=0 --threads=1'

engine = chess.engine.SimpleEngine.popen_uci("F:/leela/lc0-v0.20.2-t40B/lc0.exe")
# for each network
    # for each position
        # runPosition
        # sendResult to log
        # accumulate sumary


def main(epd_field:str,
         tcec_moves:str,
         stop_first:bool,
         found_three_times:bool,
         engine:chess.engine.SimpleEngine):

    epd_field: str = "r1r3k1/1p4p1/5p1p/PPpnp3/8/3P2P1/1B3P1P/R1R3K1 b - - "
    tcec_moves: str = " b6 "  # must start and end with a space for comparison below.
    board = chess.Board(epd_field)
    stop_first_found: bool = True
    found_three_times: bool = True
    count_found: int = 0
    info2 = []
    agree = False
    with engine.analysis(board, multipv=3, info=chess.engine.INFO_ALL) as analysis:
        for info in analysis:
            print(board.san(info['pv'][0]),info.get('score'), info.get("nodes", 0), info['time'])
            info2.append(info)
            # Unusual stop condition.
            is_first_pv:bool = info['multipv'] == 1
            if is_first_pv and " " + board.san(info['pv'][0]) in tcec_moves:
                if stop_first_found:
                    agree = True
                    break
                count_found += 1
                if found_three_times and count_found == 3:
                    agree = True
                    break
            if info.get("nodes", 0) > 400000:
                break
    turn = "W" if board.turn == chess.WHITE else "B"
    agree2 = "1" if agree else "0"
    mpv = []
    for info in analysis.multipv:
        score = str(info['score'].relative.cp)
        move = board.san(info['pv'][0])
        mpv.append([move, score])
    mpv2 = json.dumps(mpv)
    print("agree, tcec_moves, nodes, positionId, toPlay, multiPv[move, eval cp]")
    nodes = int(info.get('nodes'))
    position_id = 7777
    print(f'{agree2}, {str.strip(tcec_moves)}, {nodes}, {position_id}, {turn}, {mpv2}')
    engine.quit()
    exit

if __name__ == "__main__":
    main()
