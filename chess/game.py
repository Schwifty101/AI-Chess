from chess.pieces import Pawn, Rook, Knight, Bishop, Queen, King
from chess.board import Board
from chess.chess_ai import ChessAI

class Game:
    def __init__(self, ai_opponent=True, ai_color='black', ai_depth=3):
        self.board = Board()
        self.turn = 'white'
        self.history = []
        self.move_count = 0
        self.ai_opponent = ai_opponent
        self.ai_color = ai_color
        self.ai = ChessAI(ai_color, ai_depth)
        if self.ai_color == 'white' and ai_opponent:
            self.make_ai_move()

    def switch_turn(self):
        self.turn = 'black' if self.turn == 'white' else 'white'
        if self.turn == 'white':
            self.move_count += 1

    def in_check(self, color):
        king_pos = None
        for r in range(8):
            for c in range(8):
                piece = self.board.grid[r][c]
                if piece and isinstance(piece, King) and piece.color == color:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        opponent_color = 'black' if color == 'white' else 'white'
        return self.board.is_under_attack(king_pos, opponent_color) if king_pos else False

    def in_checkmate(self, color):
        return self.in_check(color) and not self._has_legal_moves(color)

    def in_stalemate(self, color):
        return not self.in_check(color) and not self._has_legal_moves(color)

    def _has_legal_moves(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board.grid[r][c]
                if piece and piece.color == color:
                    from_pos = (r, c)
                    for to_pos in piece.legal_moves(self.board):
                        new_board = self.board.copy()
                        new_board.move_piece(from_pos, to_pos)
                        if not self._king_in_check_after_move(new_board, color):
                            return True
        return False

    @staticmethod
    def _king_in_check_after_move(board, color):
        king_pos = None
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece and isinstance(piece, King) and piece.color == color:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        opponent_color = 'black' if color == 'white' else 'white'
        return board.is_under_attack(king_pos, opponent_color) if king_pos else False

    def undo_move(self):
        if not self.history:
            return False
        move_info = self.history.pop()
        from_pos, to_pos, captured_piece, special_move, promotion = move_info
        piece = self.board.get_piece(to_pos)
        self.board.grid[from_pos[0]][from_pos[1]] = piece
        if piece:
            piece.position = from_pos
            piece.has_moved = False if special_move in ["castling", "promotion"] else piece.has_moved
        self.board.grid[to_pos[0]][to_pos[1]] = captured_piece
        if special_move == "castling":
            if to_pos[1] > from_pos[1]:
                rook_pos = (from_pos[0], to_pos[1] - 1)
                rook = self.board.get_piece(rook_pos)
                if rook:
                    self.board.grid[rook_pos[0]][rook_pos[1]] = None
                    self.board.grid[from_pos[0]][7] = rook
                    rook.position = (from_pos[0], 7)
                    rook.has_moved = False
            else:
                rook_pos = (from_pos[0], to_pos[1] + 1)
                rook = self.board.get_piece(rook_pos)
                if rook:
                    self.board.grid[rook_pos[0]][rook_pos[1]] = None
                    self.board.grid[from_pos[0]][0] = rook
                    rook.position = (from_pos[0], 0)
                    rook.has_moved = False
        elif special_move == "en_passant":
            captured_pos = (from_pos[0], to_pos[1])
            self.board.grid[captured_pos[0]][captured_pos[1]] = captured_piece
        elif special_move == "promotion" and promotion:
            self.board.grid[from_pos[0]][from_pos[1]] = Pawn(piece.color, from_pos)
        
        # Reset en_passant_target (we don't track the previous value in the tuple)
        self.board.en_passant_target = None
        
        self.switch_turn()
        return True

    def detect_tactics(self):
        tactics = {'pins': [], 'forks': [], 'skewers': []}
        for r in range(8):
            for c in range(8):
                piece = self.board.get_piece((r, c))
                if not piece or piece.color != self.turn or isinstance(piece, King):
                    continue
                legal_moves = piece.legal_moves(self.board)
                if legal_moves:
                    all_moves_illegal = True
                    for move in legal_moves:
                        new_board = self.board.copy()
                        new_board.move_piece((r, c), move)
                        if not self._king_in_check_after_move(new_board, piece.color):
                            all_moves_illegal = False
                            break
                    if all_moves_illegal:
                        tactics['pins'].append({'piece': piece, 'position': (r, c), 'algebraic': self._pos_to_algebraic((r, c))})
        
        opponent_color = 'black' if self.turn == 'white' else 'white'
        for r in range(8):
            for c in range(8):
                piece = self.board.get_piece((r, c))
                if not piece or piece.color != opponent_color:
                    continue
                attacks = piece.legal_moves(self.board)
                attacked_pieces = []
                for attack_pos in attacks:
                    attacked = self.board.get_piece(attack_pos)
                    if attacked and attacked.color == self.turn:
                        attacked_pieces.append({'piece': attacked, 'position': attack_pos, 'algebraic': self._pos_to_algebraic(attack_pos)})
                if len(attacked_pieces) >= 2:
                    tactics['forks'].append({'attacker': piece, 'position': (r, c), 'algebraic': self._pos_to_algebraic((r, c)), 'targets': attacked_pieces})
                if isinstance(piece, (Queen, Rook, Bishop)):
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)] if isinstance(piece, Rook) else [(1, 1), (1, -1), (-1, -1), (-1, 1)] if isinstance(piece, Bishop) else [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]
                    for dr, dc in directions:
                        aligned_pieces = []
                        for i in range(1, 8):
                            check_r, check_c = r + i*dr, c + i*dc
                            if not (0 <= check_r < 8 and 0 <= check_c < 8):
                                break
                            check_piece = self.board.get_piece((check_r, check_c))
                            if check_piece and check_piece.color == self.turn:
                                aligned_pieces.append({'piece': check_piece, 'position': (check_r, check_c), 'algebraic': self._pos_to_algebraic((check_r, check_c))})
                            elif check_piece:
                                break
                        if len(aligned_pieces) >= 2:
                            piece_values = {Queen: 9, Rook: 5, Bishop: 3, Knight: 3, Pawn: 1, King: 100}
                            if piece_values[aligned_pieces[0]['piece'].__class__] > piece_values[aligned_pieces[1]['piece'].__class__]:
                                tactics['skewers'].append({'attacker': piece, 'position': (r, c), 'algebraic': self._pos_to_algebraic((r, c)), 'targets': aligned_pieces[:2]})
        return tactics

    def _pos_to_algebraic(self, pos):
        row, col = pos
        return chr(ord('a') + col) + str(8 - row)

    def play_move(self, from_pos, to_pos, promotion_piece=None):
        piece = self.board.get_piece(from_pos)
        if not piece or piece.color != self.turn or to_pos not in piece.legal_moves(self.board):
            return False
        new_board = self.board.copy()
        new_board.move_piece(from_pos, to_pos, promotion_piece)
        if self._king_in_check_after_move(new_board, self.turn):
            return False
        move_result = self.board.move_piece(from_pos, to_pos, promotion_piece)
        special_move = "castling" if isinstance(piece, King) and abs(from_pos[1] - to_pos[1]) == 2 else "promotion" if move_result['promotion'] else "en_passant" if to_pos == self.board.en_passant_target else None
        self.history.append((from_pos, to_pos, move_result['captured_piece'], special_move, promotion_piece))
        self.switch_turn()
        if self.ai_opponent and self.turn == self.ai_color:
            self.make_ai_move()
        return True

    def make_ai_move(self):
        ai_move = self.ai.choose_move(self)
        if not ai_move:
            return False
        from_pos, to_pos, promotion = ai_move
        return self.play_move(from_pos, to_pos, promotion)