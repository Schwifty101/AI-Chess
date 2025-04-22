class Piece:
    """Base class for all chess pieces."""
    def __init__(self, color, position):
        self.color = color  # 'white' or 'black'
        self.position = position  # tuple (row, col)
        self.has_moved = False

    def legal_moves(self, board):
        """Return a list of legal moves for this piece on the given board."""
        raise NotImplementedError

    def move(self, new_position):
        """Update piece position."""
        self.position = new_position
        self.has_moved = True

class Pawn(Piece):
    def legal_moves(self, board):
        moves = []
        row, col = self.position
        direction = -1 if self.color == 'white' else 1
        
        # Single square advance
        new_pos = (row + direction, col)
        if board.is_in_bounds(new_pos) and board.get_piece(new_pos) is None:
            moves.append(new_pos)
            
            # Double square advance (first move only)
            if not self.has_moved:
                new_pos = (row + 2 * direction, col)
                if board.is_in_bounds(new_pos) and board.get_piece(new_pos) is None:
                    moves.append(new_pos)
        
        # Diagonal captures
        for dc in [-1, 1]:
            new_pos = (row + direction, col + dc)
            if board.is_in_bounds(new_pos):
                piece = board.get_piece(new_pos)
                if piece and piece.color != self.color:
                    moves.append(new_pos)
                elif new_pos == board.en_passant_target:
                    moves.append(new_pos)
        
        return moves

class Rook(Piece):
    def legal_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_pos = (row + i * dr, col + i * dc)
                if not board.is_in_bounds(new_pos):
                    break
                piece = board.get_piece(new_pos)
                if piece is None:
                    moves.append(new_pos)
                elif piece.color != self.color:
                    moves.append(new_pos)
                    break
                else:
                    break
        return moves

class Knight(Piece):
    def legal_moves(self, board):
        moves = []
        row, col = self.position
        knight_moves = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
        
        for dr, dc in knight_moves:
            new_pos = (row + dr, col + dc)
            if board.is_in_bounds(new_pos):
                piece = board.get_piece(new_pos)
                if piece is None or piece.color != self.color:
                    moves.append(new_pos)
        return moves

class Bishop(Piece):
    def legal_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_pos = (row + i * dr, col + i * dc)
                if not board.is_in_bounds(new_pos):
                    break
                piece = board.get_piece(new_pos)
                if piece is None:
                    moves.append(new_pos)
                elif piece.color != self.color:
                    moves.append(new_pos)
                    break
                else:
                    break
        return moves

class Queen(Piece):
    def legal_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_pos = (row + i * dr, col + i * dc)
                if not board.is_in_bounds(new_pos):
                    break
                piece = board.get_piece(new_pos)
                if piece is None:
                    moves.append(new_pos)
                elif piece.color != self.color:
                    moves.append(new_pos)
                    break
                else:
                    break
        return moves

class King(Piece):
    def legal_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        
        for dr, dc in directions:
            new_pos = (row + dr, col + dc)
            if board.is_in_bounds(new_pos):
                piece = board.get_piece(new_pos)
                if piece is None or piece.color != self.color:
                    # Check if the new position would put kings adjacent
                    if not self._adjacent_to_enemy_king(board, new_pos):
                        moves.append(new_pos)
        
        if not self.has_moved and not board.is_under_attack(self.position, 'white' if self.color == 'black' else 'black', ignore_king=True):
            kingside = self._get_kingside_castling_moves(board)
            if kingside:
                moves.append(kingside)
            queenside = self._get_queenside_castling_moves(board)
            if queenside:
                moves.append(queenside)
        
        return moves
    
    def _adjacent_to_enemy_king(self, board, pos):
        """Check if the given position is adjacent to the opponent's king"""
        opponent_color = 'white' if self.color == 'black' else 'black'
        
        # Find opponent's king
        opponent_king_pos = None
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece and isinstance(piece, King) and piece.color == opponent_color:
                    opponent_king_pos = (r, c)
                    break
            if opponent_king_pos:
                break
                
        if not opponent_king_pos:
            return False
            
        # Check if the two positions are adjacent
        row_diff = abs(pos[0] - opponent_king_pos[0])
        col_diff = abs(pos[1] - opponent_king_pos[1])
        
        return row_diff <= 1 and col_diff <= 1
    
    def _get_kingside_castling_moves(self, board):
        row, col = self.position
        rook_pos = (row, 7)
        rook = board.get_piece(rook_pos)
        if not (isinstance(rook, Rook) and rook.color == self.color and not rook.has_moved):
            return None
        for c in range(col + 1, 7):
            if board.get_piece((row, c)) is not None:
                return None
        opponent_color = 'white' if self.color == 'black' else 'black'
        for c in range(col, col + 3):
            if board.is_square_attacked((row, c), opponent_color):
                return None
        return (row, col + 2)
    
    def _get_queenside_castling_moves(self, board):
        row, col = self.position
        rook_pos = (row, 0)
        rook = board.get_piece(rook_pos)
        if not (isinstance(rook, Rook) and rook.color == self.color and not rook.has_moved):
            return None
        for c in range(1, col):
            if board.get_piece((row, c)) is not None:
                return None
        opponent_color = 'white' if self.color == 'black' else 'black'
        for c in range(col - 2, col + 1):
            if board.is_square_attacked((row, c), opponent_color):
                return None
        return (row, col - 2)