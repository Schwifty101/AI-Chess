import copy
from chess.pieces import Pawn, Rook, Knight, Bishop, Queen, King

class Board:
    """Represents the 8x8 chess board and holds piece positions."""
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self._setup_pieces()
        self.en_passant_target = None

    def _setup_pieces(self):
        for col in range(8):
            self.grid[1][col] = Pawn('black', (1, col))
            self.grid[6][col] = Pawn('white', (6, col))
        self.grid[0][0] = Rook('black', (0, 0))
        self.grid[0][7] = Rook('black', (0, 7))
        self.grid[7][0] = Rook('white', (7, 0))
        self.grid[7][7] = Rook('white', (7, 7))
        self.grid[0][1] = Knight('black', (0, 1))
        self.grid[0][6] = Knight('black', (0, 6))
        self.grid[7][1] = Knight('white', (7, 1))
        self.grid[7][6] = Knight('white', (7, 6))
        self.grid[0][2] = Bishop('black', (0, 2))
        self.grid[0][5] = Bishop('black', (0, 5))
        self.grid[7][2] = Bishop('white', (7, 2))
        self.grid[7][5] = Bishop('white', (7, 5))
        self.grid[0][3] = Queen('black', (0, 3))
        self.grid[7][3] = Queen('white', (7, 3))
        self.grid[0][4] = King('black', (0, 4))
        self.grid[7][4] = King('white', (7, 4))

    def is_in_bounds(self, pos):
        r, c = pos
        return 0 <= r < 8 and 0 <= c < 8

    def get_piece(self, pos):
        r, c = pos
        return self.grid[r][c]

    def move_piece(self, from_pos, to_pos, promotion_piece=None):
        piece = self.get_piece(from_pos)
        if not piece:
            return False
        captured_piece = self.get_piece(to_pos)
        previous_en_passant = self.en_passant_target
        self.en_passant_target = None
        
        if isinstance(piece, Pawn) and to_pos == self.en_passant_target:
            captured_pos = (from_pos[0], to_pos[1])
            captured_piece = self.grid[captured_pos[0]][captured_pos[1]]
            self.grid[captured_pos[0]][captured_pos[1]] = None
        
        if isinstance(piece, Pawn) and abs(from_pos[0] - to_pos[0]) == 2:
            direction = -1 if piece.color == 'white' else 1
            self.en_passant_target = (to_pos[0] - direction, to_pos[1])
        
        rook_move = None
        if isinstance(piece, King) and abs(from_pos[1] - to_pos[1]) == 2:
            if to_pos[1] > from_pos[1]:
                rook_from = (from_pos[0], 7)
                rook_to = (from_pos[0], to_pos[1] - 1)
            else:
                rook_from = (from_pos[0], 0)
                rook_to = (from_pos[0], to_pos[1] + 1)
            rook = self.get_piece(rook_from)
            self.grid[rook_to[0]][rook_to[1]] = rook
            self.grid[rook_from[0]][rook_from[1]] = None
            rook.move(rook_to)
            rook_move = (rook_from, rook_to, rook)
        
        self.grid[to_pos[0]][to_pos[1]] = piece
        self.grid[from_pos[0]][from_pos[1]] = None
        original_piece = piece
        piece.move(to_pos)
        
        promoted_piece = None
        if isinstance(piece, Pawn) and ((piece.color == 'white' and to_pos[0] == 0) or (piece.color == 'black' and to_pos[0] == 7)):
            if promotion_piece in ['Q', 'R', 'B', 'N']:
                if promotion_piece == 'Q':
                    self.grid[to_pos[0]][to_pos[1]] = Queen(piece.color, to_pos)
                elif promotion_piece == 'R':
                    self.grid[to_pos[0]][to_pos[1]] = Rook(piece.color, to_pos)
                elif promotion_piece == 'B':
                    self.grid[to_pos[0]][to_pos[1]] = Bishop(piece.color, to_pos)
                elif promotion_piece == 'N':
                    self.grid[to_pos[0]][to_pos[1]] = Knight(piece.color, to_pos)
            else:
                self.grid[to_pos[0]][to_pos[1]] = Queen(piece.color, to_pos)
            promoted_piece = self.grid[to_pos[0]][to_pos[1]]
        
        return {
            'from_pos': from_pos,
            'to_pos': to_pos,
            'original_piece': original_piece,
            'captured_piece': captured_piece,
            'promotion': promoted_piece,
            'castling': rook_move,
            'previous_en_passant': previous_en_passant
        }

    def is_under_attack(self, pos, attacker_color, ignore_king=False):
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.color == attacker_color and not (ignore_king and isinstance(piece, King)):
                    if isinstance(piece, Pawn):
                        row, col = piece.position
                        direction = -1 if piece.color == 'white' else 1
                        attack_positions = [(row + direction, col - 1), (row + direction, col + 1)]
                        if pos in attack_positions and self.is_in_bounds(pos):
                            return True
                    elif isinstance(piece, Knight):
                        row, col = piece.position
                        knight_moves = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
                        for dr, dc in knight_moves:
                            if (row + dr, col + dc) == pos:
                                return True
                    else:
                        if self._is_attacked_by_sliding_piece(piece, pos):
                            return True
        return False

    def is_square_attacked(self, pos, attacker_color):
        return self.is_under_attack(pos, attacker_color, ignore_king=True)

    def _is_attacked_by_sliding_piece(self, piece, target_pos):
        piece_type = piece.__class__.__name__
        piece_pos = piece.position
        is_rook_attack = piece_type in ['Rook', 'Queen'] and (piece_pos[0] == target_pos[0] or piece_pos[1] == target_pos[1])
        is_bishop_attack = piece_type in ['Bishop', 'Queen'] and abs(piece_pos[0] - target_pos[0]) == abs(piece_pos[1] - target_pos[1])
        if not (is_rook_attack or is_bishop_attack):
            return False
        row_step = 0 if piece_pos[0] == target_pos[0] else (1 if target_pos[0] > piece_pos[0] else -1)
        col_step = 0 if piece_pos[1] == target_pos[1] else (1 if target_pos[1] > piece_pos[1] else -1)
        current_row, current_col = piece_pos
        while True:
            current_row += row_step
            current_col += col_step
            if (current_row, current_col) == target_pos:
                return True
            if self.is_in_bounds((current_row, current_col)) and self.grid[current_row][current_col] is not None:
                return False

    def copy(self):
        new_board = Board()
        new_board.grid = [[None for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece:
                    if isinstance(piece, Pawn):
                        new_piece = Pawn(piece.color, (r, c))
                    elif isinstance(piece, Rook):
                        new_piece = Rook(piece.color, (r, c))
                    elif isinstance(piece, Knight):
                        new_piece = Knight(piece.color, (r, c))
                    elif isinstance(piece, Bishop):
                        new_piece = Bishop(piece.color, (r, c))
                    elif isinstance(piece, Queen):
                        new_piece = Queen(piece.color, (r, c))
                    elif isinstance(piece, King):
                        new_piece = King(piece.color, (r, c))
                    new_piece.has_moved = piece.has_moved
                    new_board.grid[r][c] = new_piece
        new_board.en_passant_target = self.en_passant_target
        return new_board 