import chess
import chess.engine

engine = chess.engine.SimpleEngine.popen_uci('F:/leela/lc0-v0.20.2-t40B/lc0.exe')

board = chess.Board()
while not board.is_game_over():
    result = engine.play(board, chess.engine.Limit(time=0.100))
    board.push(result.move)

engine.quit()
