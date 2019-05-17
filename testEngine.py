from typing import List, Any
import chess.engine
import json

engine = chess.engine.SimpleEngine.popen_uci("F:/leela/lc0-v0.20.2-t40B/lc0.exe")


class LogInfo:
    """
    info for one pv of analysis with selected fields
    """

    def __init__(self, info: chess.engine.SimpleAnalysisResult.info, board: chess.Board):
        """

        :type info: chess.engine.SimpleAnalysisResult.info
        """

        self._algebraic = board.san(info['pv'][0])


def main():
    epd_field: str = "r1r3k1/1p4p1/5p1p/PPpnp3/8/3P2P1/1B3P1P/R1R3K1 b - - "
    tcec_moves: str = " Kf7 Nb4 "  # must start and end with a space for comparison below.
    board = chess.Board(epd_field)
    stop_first_found: bool = True
    found_three_times: bool = True
    count_found: int = 0
    info2 = []
    agree = False
    with engine.analysis(board, multipv=3, info=chess.engine.INFO_ALL) as analysis:
        for info in analysis:
            print(board.san(info['pv'][0]), info.get("nodes", 0), info['time'])
            info2.append(info)
            # Unusual stop condition.
            if " " + board.san(info['pv'][0]) in tcec_moves:
                if stop_first_found:
                    agree = True
                    break
                count_found += 1
                if found_three_times and count_found == 3:
                    agree = True
                    break
            if info.get("nodes", 0) > 800:
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
    print(agree2, ",", tcec_moves, ",", info.get('nodes'),",", 7777, ",", turn, ",", mpv2)
    engine.quit()
    exit

if __name__ == "__main__":
    main()
