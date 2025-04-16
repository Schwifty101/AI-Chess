import random
import copy
import time
from chess.pieces import Pawn, Rook, Knight, Bishop, Queen, King

class ChessAI:
    """AI opponent for the chess game using minimax with alpha-beta pruning."""
    def __init__(self, color, search_depth=3):
        self.color = color
        self.opponent_color = 'black' if color == 'white' else 'white'
        self.search_depth = search_depth
        self.max_depth = search_depth + 3  # Maximum depth for complex positions
        self.min_depth = max(1, search_depth - 1)  # Minimum depth for simple positions
        self.quiescence_depth = 3  # Maximum depth for quiescence search
        self.transposition_table = {}  # Store previously evaluated positions
        self.nodes_evaluated = 0  # For performance tracking
        self.piece_values = {'Pawn': 100, 'Knight': 320, 'Bishop': 330, 'Rook': 500, 'Queen': 900, 'King': 20000}
        # Killer move heuristic - store moves that caused beta cutoffs
        self.killer_moves = [[None, None] for _ in range(self.max_depth + 1)]
        # History heuristic - track effectiveness of each move across positions
        self.history_table = {}
        # Principal Variation tracking
        self.pv_table = {}
        # Previous iteration's evaluation for adaptive depth
        self.previous_eval = 0
        self.position_values = {
            'Pawn': [[0,0,0,0,0,0,0,0],[50,50,50,50,50,50,50,50],[10,10,20,30,30,20,10,10],[5,5,10,25,25,10,5,5],[0,0,0,20,20,0,0,0],[5,-5,-10,0,0,-10,-5,5],[5,10,10,-20,-20,10,10,5],[0,0,0,0,0,0,0,0]],
            'Knight': [[-50,-40,-30,-30,-30,-30,-40,-50],[-40,-20,0,0,0,0,-20,-40],[-30,0,10,15,15,10,0,-30],[-30,5,15,20,20,15,5,-30],[-30,0,15,20,20,15,0,-30],[-30,5,10,15,15,10,5,-30],[-40,-20,0,5,5,0,-20,-40],[-50,-40,-30,-30,-30,-30,-40,-50]],
            'Bishop': [[-20,-10,-10,-10,-10,-10,-10,-20],[-10,0,0,0,0,0,0,-10],[-10,0,10,10,10,10,0,-10],[-10,5,5,10,10,5,5,-10],[-10,0,5,10,10,5,0,-10],[-10,5,5,5,5,5,5,-10],[-10,0,5,0,0,5,0,-10],[-20,-10,-10,-10,-10,-10,-10,-20]],
            'Rook': [[0,0,0,0,0,0,0,0],[5,10,10,10,10,10,10,5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[0,0,0,5,5,0,0,0]],
            'Queen': [[-20,-10,-10,-5,-5,-10,-10,-20],[-10,0,0,0,0,0,0,-10],[-10,0,5,5,5,5,0,-10],[-5,0,5,5,5,5,0,-5],[0,0,5,5,5,5,0,-5],[-10,5,5,5,5,5,0,-10],[-10,0,5,0,0,0,0,-10],[-20,-10,-10,-5,-5,-10,-10,-20]],
            'King': [[-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],[-20,-30,-30,-40,-40,-30,-30,-20],[-10,-20,-20,-20,-20,-20,-20,-10],[20,20,0,0,0,0,20,20],[20,30,10,0,0,10,30,20]]
        }
        self.king_endgame_values = [[-50,-40,-30,-20,-20,-30,-40,-50],[-30,-20,-10,0,0,-10,-20,-30],[-30,-10,20,30,30,20,-10,-30],[-30,-10,30,40,40,30,-10,-30],[-30,-10,30,40,40,30,-10,-30],[-30,-10,20,30,30,20,-10,-30],[-30,-30,0,0,0,0,-30,-30],[-50,-30,-30,-30,-30,-30,-30,-50]]

    def choose_move(self, game):
        self.nodes_evaluated = 0
        self.transposition_table = {}
        # Reset killer move and history heuristic for new search
        self.killer_moves = [[None, None] for _ in range(self.max_depth + 1)]
        self.pv_table = {}
        start_time = time.time()
        
        legal_moves = self._get_all_legal_moves(game, self.color)
        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # Use iterative deepening to get better move ordering for deeper searches
        best_move = None
        best_score = float('-inf')
        
        # Initial PV move ordering for first iteration
        legal_moves = self._sort_moves(game, legal_moves)
        
        for current_depth in range(1, self.search_depth + 1):
            print(f"Searching at depth {current_depth}...")
            
            # Adaptive depth: adjust based on position complexity
            adaptive_depth = self._get_adaptive_depth(game, legal_moves, current_depth)
            
            # Alpha-beta window
            alpha = float('-inf')
            beta = float('inf')
            
            # Reset PV table for this iteration
            self.pv_table = {}
            
            # Sort moves based on previous iteration results
            legal_moves = self._sort_moves_with_history(game, legal_moves, current_depth)
            
            # Search each move at the current depth
            current_best_move = None
            current_best_score = float('-inf')
            
            for move in legal_moves:
                from_pos, to_pos, promotion = move
                game_copy = self._copy_game(game)
                game_copy.play_move(from_pos, to_pos, promotion)
                
                # Get score from minimax
                score = self._minimax(game_copy, adaptive_depth - 1, alpha, beta, False, 0)
                
                # Update best move if found
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move
                    
                    # Update history table - increase score for this move
                    move_key = self._get_move_key(from_pos, to_pos)
                    if move_key not in self.history_table:
                        self.history_table[move_key] = 0
                    self.history_table[move_key] += current_depth * current_depth
                
                alpha = max(alpha, current_best_score)
            
            # Update overall best move if we completed this iteration
            if current_best_move:
                best_move = current_best_move
                best_score = current_best_score
                
                # Store this evaluation for adaptive depth in next iteration
                eval_diff = abs(best_score - self.previous_eval)
                self.previous_eval = best_score
                
                print(f"Depth {current_depth}: Best move {best_move}, Score: {best_score}")
            
            # If we're running out of time or found a forced mate, break early
            if time.time() - start_time > 5 or abs(best_score) > 90000:  # 5 second time limit
                break
        
        # Print statistics
        print(f"Nodes evaluated: {self.nodes_evaluated}, Time: {time.time() - start_time:.2f}s")
        return best_move

    def _get_adaptive_depth(self, game, legal_moves, base_depth):
        """Enhanced adaptive depth calculation based on position complexity"""
        # Fewer moves = can search deeper
        move_count_factor = max(0.5, min(1.5, 10 / max(1, len(legal_moves))))
        
        # In check = search deeper
        check_factor = 1.3 if game.in_check(self.color) else 1.0
        
        # Endgame = search deeper
        endgame_factor = 1.3 if self._is_endgame(game.board) else 1.0
        
        # Tactical positions (where lots of captures are available) = search deeper
        tactical_factor = 1.0
        capture_moves = self._get_capture_moves(game, self.color)
        if len(capture_moves) > 3:
            tactical_factor = 1.2
        
        # Unstable evaluation (big change from previous iteration) = search deeper
        eval_stability_factor = 1.0
        current_eval = self._evaluate_position(game)
        eval_diff = abs(current_eval - self.previous_eval)
        if eval_diff > 200:  # significant evaluation change
            eval_stability_factor = 1.25
        
        # Material imbalance = search deeper
        material_imbalance = self._get_material_imbalance(game.board)
        material_factor = 1.0 + min(0.3, material_imbalance / 1000.0)
        
        # Calculate adaptive depth with all factors
        adaptive_depth = base_depth * move_count_factor * check_factor * endgame_factor * tactical_factor * eval_stability_factor * material_factor
        
        # Ensure depth stays within bounds
        actual_depth = min(self.max_depth, max(self.min_depth, round(adaptive_depth)))
        
        # Debug information 
        if base_depth > 1:
            print(f"Adaptive depth: {actual_depth} (from base {base_depth})")
            
        return actual_depth
        
    def _get_material_imbalance(self, board):
        """Calculate the material imbalance on the board"""
        ai_material = 0
        opponent_material = 0
        
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if not piece:
                    continue
                    
                piece_value = self.piece_values.get(piece.__class__.__name__, 0)
                if piece.color == self.color:
                    ai_material += piece_value
                else:
                    opponent_material += piece_value
                    
        return abs(ai_material - opponent_material)

    def _minimax(self, game, depth, alpha, beta, is_maximizing, ply):
        """Enhanced minimax implementation with alpha-beta pruning"""
        self.nodes_evaluated += 1
        
        # Check for immediate terminal states
        if game.in_checkmate(game.turn):
            return -100000 if is_maximizing else 100000
        if game.in_stalemate(game.turn):
            return 0
            
        # Use transposition table for position lookup
        board_hash = self._get_board_hash(game.board)
        if board_hash in self.transposition_table and self.transposition_table[board_hash][0] >= depth:
            stored_depth, stored_value, value_type = self.transposition_table[board_hash]
            if value_type == 0:  # Exact value
                return stored_value
            elif value_type == 1 and stored_value <= alpha:  # Upper bound
                return alpha
            elif value_type == -1 and stored_value >= beta:  # Lower bound
                return beta
        
        # Base case: reached depth limit
        if depth <= 0:
            # Use quiescence search to handle capture sequences and avoid horizon effect
            return self._quiescence_search(game, alpha, beta, is_maximizing, 0)
            
        # Determine whose turn it is
        is_current_player = (game.turn == self.color) == is_maximizing
        color = self.color if is_current_player else self.opponent_color
        
        # Get all legal moves for current position
        legal_moves = self._get_all_legal_moves(game, color)
        if not legal_moves:
            return self._evaluate_position(game)
            
        # Sort moves using PV, killer move, and history heuristics
        legal_moves = self._sort_moves_with_history(game, legal_moves, depth, ply)
        
        # Flag for transposition table
        value_type = 0  # 0: exact, 1: upper bound, -1: lower bound
        best_move = None
        
        if is_maximizing:
            max_score = float('-inf')
            for move in legal_moves:
                from_pos, to_pos, promotion = move
                game_copy = self._copy_game(game)
                game_copy.play_move(from_pos, to_pos, promotion)
                
                score = self._minimax(game_copy, depth - 1, alpha, beta, False, ply + 1)
                
                if score > max_score:
                    max_score = score
                    best_move = move
                    
                alpha = max(alpha, max_score)
                
                # Store in PV table if this is the best move so far
                if best_move:
                    self.pv_table[(board_hash, depth)] = best_move
                
                # Beta cutoff - store killer move
                if beta <= alpha:
                    if not self._is_capture(game.board, from_pos, to_pos):
                        # Only store quiet moves as killer moves
                        self._store_killer_move(move, ply)
                    
                    # Update history heuristic for this move
                    move_key = self._get_move_key(from_pos, to_pos)
                    self.history_table[move_key] = self.history_table.get(move_key, 0) + depth * depth
                    
                    value_type = -1  # Lower bound
                    break
                    
            # Store result in transposition table
            self.transposition_table[board_hash] = (depth, max_score, value_type)
            return max_score
        else:
            min_score = float('inf')
            for move in legal_moves:
                from_pos, to_pos, promotion = move
                game_copy = self._copy_game(game)
                game_copy.play_move(from_pos, to_pos, promotion)
                
                score = self._minimax(game_copy, depth - 1, alpha, beta, True, ply + 1)
                
                if score < min_score:
                    min_score = score
                    best_move = move
                    
                beta = min(beta, min_score)
                
                # Store in PV table if this is the best move so far
                if best_move:
                    self.pv_table[(board_hash, depth)] = best_move
                
                # Alpha cutoff - store killer move
                if beta <= alpha:
                    if not self._is_capture(game.board, from_pos, to_pos):
                        # Only store quiet moves as killer moves
                        self._store_killer_move(move, ply)
                    
                    # Update history heuristic for this move
                    move_key = self._get_move_key(from_pos, to_pos)
                    self.history_table[move_key] = self.history_table.get(move_key, 0) + depth * depth
                    
                    value_type = 1  # Upper bound
                    break
                    
            # Store result in transposition table
            self.transposition_table[board_hash] = (depth, min_score, value_type)
            return min_score

    def _get_board_hash(self, board):
        """Create a hash of the board position for the transposition table"""
        # Create a simplified string representation of the board
        board_str = ""
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece:
                    piece_code = piece.__class__.__name__[0].lower()
                    if piece.__class__.__name__ == 'Knight':
                        piece_code = 'n'
                    if piece.color == 'white':
                        piece_code = piece_code.upper()
                    board_str += piece_code
                else:
                    board_str += ' '
        # Include en_passant_target if exists
        if board.en_passant_target:
            board_str += f"e{board.en_passant_target[0]}{board.en_passant_target[1]}"
        return hash(board_str)
        
    def _quiescence_search(self, game, alpha, beta, is_maximizing, ply_from_root):
        """Search capture moves until a quiet position is reached"""
        self.nodes_evaluated += 1
        
        # Static evaluation of the current position
        stand_pat = self._evaluate_position(game)
        
        # Early return conditions
        if stand_pat >= beta and is_maximizing:
            return beta
        if stand_pat <= alpha and not is_maximizing:
            return alpha
        
        # Update alpha/beta bounds
        if is_maximizing and stand_pat > alpha:
            alpha = stand_pat
        if not is_maximizing and stand_pat < beta:
            beta = stand_pat
        
        # Stop quiescence search if we've reached maximum depth
        if ply_from_root >= self.quiescence_depth:
            return stand_pat
        
        # Get and sort capturing moves
        color = self.color if (game.turn == self.color) == is_maximizing else self.opponent_color
        capture_moves = self._get_capture_moves(game, color)
        
        # No captures available, return static evaluation
        if not capture_moves:
            return stand_pat
        
        # Sort captures by MVV-LVA
        capture_moves = self._sort_tactical_moves(game, capture_moves)
        
        if is_maximizing:
            for move in capture_moves:
                from_pos, to_pos, promotion = move
                
                # Static Exchange Evaluation (SEE) pruning
                # Skip captures that lose material
                if not self._is_favorable_capture(game.board, from_pos, to_pos):
                    continue
                
                game_copy = self._copy_game(game)
                game_copy.play_move(from_pos, to_pos, promotion)
                
                score = self._quiescence_search(game_copy, alpha, beta, False, ply_from_root + 1)
                stand_pat = max(stand_pat, score)
                alpha = max(alpha, stand_pat)
                
                if alpha >= beta:
                    break
        else:
            for move in capture_moves:
                from_pos, to_pos, promotion = move
                
                # Static Exchange Evaluation (SEE) pruning
                # Skip captures that lose material
                if not self._is_favorable_capture(game.board, from_pos, to_pos):
                    continue
                
                game_copy = self._copy_game(game)
                game_copy.play_move(from_pos, to_pos, promotion)
                
                score = self._quiescence_search(game_copy, alpha, beta, True, ply_from_root + 1)
                stand_pat = min(stand_pat, score)
                beta = min(beta, stand_pat)
                
                if alpha >= beta:
                    break
        
        return stand_pat

    def _get_capture_moves(self, game, color):
        """Get only capturing moves for quiescence search"""
        capture_moves = []
        for r in range(8):
            for c in range(8):
                piece = game.board.grid[r][c]
                if piece and piece.color == color:
                    from_pos = (r, c)
                    moves = piece.legal_moves(game.board)
                    for to_pos in moves:
                        # Only include captures
                        target_piece = game.board.get_piece(to_pos)
                        if target_piece:
                            if isinstance(piece, Pawn) and ((piece.color == 'white' and to_pos[0] == 0) or 
                                                          (piece.color == 'black' and to_pos[0] == 7)):
                                for promotion in ['Q', 'R', 'B', 'N']:
                                    new_board = game.board.copy()
                                    new_board.move_piece(from_pos, to_pos, promotion)
                                    if not self._king_in_check(new_board, color):
                                        capture_moves.append((from_pos, to_pos, promotion))
                            else:
                                new_board = game.board.copy()
                                new_board.move_piece(from_pos, to_pos)
                                if not self._king_in_check(new_board, color):
                                    capture_moves.append((from_pos, to_pos, None))
        return capture_moves

    def _get_all_legal_moves(self, game, color):
        legal_moves = []
        for r in range(8):
            for c in range(8):
                piece = game.board.grid[r][c]
                if piece and piece.color == color:
                    from_pos = (r, c)
                    moves = piece.legal_moves(game.board)
                    for to_pos in moves:
                        if isinstance(piece, Pawn) and ((piece.color == 'white' and to_pos[0] == 0) or (piece.color == 'black' and to_pos[0] == 7)):
                            for promotion in ['Q', 'R', 'B', 'N']:
                                new_board = game.board.copy()
                                new_board.move_piece(from_pos, to_pos, promotion)
                                if not self._king_in_check(new_board, color):
                                    legal_moves.append((from_pos, to_pos, promotion))
                        else:
                            new_board = game.board.copy()
                            new_board.move_piece(from_pos, to_pos)
                            if not self._king_in_check(new_board, color):
                                legal_moves.append((from_pos, to_pos, None))
        return legal_moves

    def _king_in_check(self, board, color):
        king_pos = None
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece and piece.__class__.__name__ == 'King' and piece.color == color:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        opponent_color = 'black' if color == 'white' else 'white'
        return board.is_under_attack(king_pos, opponent_color) if king_pos else False

    def _evaluate_position(self, game):
        if game.in_checkmate(self.color):
            return -100000
        elif game.in_checkmate(self.opponent_color):
            return 100000
        elif game.in_stalemate(game.turn):
            return 0
        material_score = 0
        position_score = 0
        is_endgame = self._is_endgame(game.board)
        for r in range(8):
            for c in range(8):
                piece = game.board.grid[r][c]
                if not piece:
                    continue
                piece_value = self.piece_values.get(piece.__class__.__name__, 0)
                pos_value = 0
                piece_type = piece.__class__.__name__
                if piece_type in self.position_values:
                    pos_value = self.position_values[piece_type][7-r][c] if piece.color == 'black' else self.position_values[piece_type][r][c]
                if piece_type == 'King' and is_endgame:
                    pos_value = self.king_endgame_values[7-r][c] if piece.color == 'black' else self.king_endgame_values[r][c]
                value_factor = 1 if piece.color == self.color else -1
                material_score += value_factor * piece_value
                position_score += value_factor * pos_value
        mobility_score = self._evaluate_mobility(game)
        king_safety = self._evaluate_king_safety(game)
        pawn_structure = self._evaluate_pawn_structure(game)
        return (material_score * 1.0 + position_score * 0.1 + mobility_score * 0.2 + king_safety * 0.3 + pawn_structure * 0.1)

    def _evaluate_mobility(self, game):
        ai_moves = len(self._get_all_legal_moves(game, self.color))
        opponent_moves = len(self._get_all_legal_moves(game, self.opponent_color))
        return ai_moves - opponent_moves

    def _evaluate_king_safety(self, game):
        ai_in_check = game.in_check(self.color)
        opponent_in_check = game.in_check(self.opponent_color)
        return -30 if ai_in_check else (20 if opponent_in_check else 0)

    def _evaluate_pawn_structure(self, game):
        ai_pawns = opponent_pawns = 0
        for r in range(8):
            for c in range(8):
                piece = game.board.grid[r][c]
                if piece and piece.__class__.__name__ == 'Pawn':
                    if piece.color == self.color:
                        ai_pawns += 1
                    else:
                        opponent_pawns += 1
        return (ai_pawns - opponent_pawns) * 10

    def _is_endgame(self, board):
        white_major = black_major = 0
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece and piece.__class__.__name__ in ['Queen', 'Rook']:
                    if piece.color == 'white':
                        white_major += 1
                    else:
                        black_major += 1
        return white_major <= 1 and black_major <= 1

    def _copy_game(self, game):
        # Create a new game instance with the same settings
        new_game = type(game)(ai_opponent=False, ai_color=game.ai_color, ai_depth=game.ai.search_depth)
        
        # Copy board state manually instead of using deepcopy
        new_game.board = game.board.copy()
        new_game.turn = game.turn
        new_game.move_count = game.move_count
        
        # Don't copy history as it's not needed for evaluation
        new_game.history = []
        
        return new_game

    def _sort_moves(self, game, moves):
        move_scores = []
        for from_pos, to_pos, promotion in moves:
            score = 0
            moving_piece = game.board.get_piece(from_pos)
            captured_piece = game.board.get_piece(to_pos)
            
            # 1. Score captures using MVV-LVA (Most Valuable Victim - Least Valuable Aggressor)
            if captured_piece:
                captured_value = self.piece_values.get(captured_piece.__class__.__name__, 0)
                moving_value = self.piece_values.get(moving_piece.__class__.__name__, 0)
                # MVV-LVA: prioritize capturing valuable pieces with less valuable pieces
                score = 10000 + 10 * captured_value - moving_value
                
                # Additional score for "winning" captures (captured piece more valuable)
                if captured_value > moving_value:
                    score += 500
            
            # 2. Score checks (moving to check the opponent's king)
            new_board = game.board.copy()
            new_board.move_piece(from_pos, to_pos, promotion)
            opponent = 'black' if moving_piece.color == 'white' else 'white'
            if self._results_in_check(new_board, opponent):
                score += 9000
                
                # Check if the move also results in discovered check (extremely valuable)
                if self._is_discovered_check(game.board, from_pos, to_pos, moving_piece.color):
                    score += 500
            
            # 3. Score promotions
            if promotion:
                promo_values = {'Q': 900, 'R': 500, 'B': 330, 'N': 320}
                score += 8000 + promo_values.get(promotion, 0)
            
            # 4. Score central control (bonus for moves to central squares)
            central_squares = [(3,3), (3,4), (4,3), (4,4)]
            near_central = [(2,2), (2,3), (2,4), (2,5), (3,2), (3,5), (4,2), (4,5), (5,2), (5,3), (5,4), (5,5)]
            
            if to_pos in central_squares:
                score += 50
            elif to_pos in near_central:
                score += 25
                
            # 5. Score development moves in opening
            if game.move_count < 10 and isinstance(moving_piece, (Knight, Bishop)) and not moving_piece.has_moved:
                score += 30
                
            # 6. Penalize moving king in opening/middlegame unless castling
            if isinstance(moving_piece, King) and not self._is_endgame(game.board):
                if abs(from_pos[1] - to_pos[1]) == 2:  # Castling
                    score += 60
                else:
                    score -= 40
                    
            move_scores.append((score, (from_pos, to_pos, promotion)))
            
        move_scores.sort(reverse=True)
        return [move for _, move in move_scores]
        
    def _results_in_check(self, board, color):
        """Check if the given color's king is in check on the board"""
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
        
    def _is_discovered_check(self, board, from_pos, to_pos, moving_color):
        """Check if moving the piece would reveal a discovered check"""
        opponent_color = 'black' if moving_color == 'white' else 'white'
        
        # Temporarily remove the piece
        moving_piece = board.get_piece(from_pos)
        board.grid[from_pos[0]][from_pos[1]] = None
        
        # Check if any piece from moving_color can now check opponent's king
        king_pos = None
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece and isinstance(piece, King) and piece.color == opponent_color:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
                
        result = board.is_under_attack(king_pos, moving_color) if king_pos else False
        
        # Restore the piece
        board.grid[from_pos[0]][from_pos[1]] = moving_piece
        
        return result

    def _sort_moves_with_history(self, game, moves, depth, ply=0):
        """Sort moves using PV, killer moves, and history heuristic"""
        move_scores = []
        board_hash = self._get_board_hash(game.board)
        
        for from_pos, to_pos, promotion in moves:
            score = 0
            moving_piece = game.board.get_piece(from_pos)
            target_piece = game.board.get_piece(to_pos)
            move_key = self._get_move_key(from_pos, to_pos)
            
            # 1. Principal Variation - highest priority
            # If this move was the best move at this depth in a previous iteration, prioritize it
            if (board_hash, depth) in self.pv_table and self.pv_table[(board_hash, depth)] == (from_pos, to_pos, promotion):
                score += 100000
            
            # 2. Captures - use MVV-LVA ordering
            if target_piece:
                target_value = self.piece_values.get(target_piece.__class__.__name__, 0)
                attacker_value = self.piece_values.get(moving_piece.__class__.__name__, 0)
                score += 10000 + (10 * target_value - attacker_value)
                
                # Extra score for good captures (SEE)
                if self._is_favorable_capture(game.board, from_pos, to_pos):
                    score += 500
            
            # 3. Killer moves
            if self._is_killer_move((from_pos, to_pos, promotion), ply):
                score += 9000
            
            # 4. History heuristic
            if move_key in self.history_table:
                score += min(self.history_table[move_key], 8000)  # Cap to avoid overriding higher priority moves
            
            # 5. Promotions
            if promotion:
                promo_values = {'Q': 900, 'R': 500, 'B': 330, 'N': 320}
                score += 8500 + promo_values.get(promotion, 0)
            
            # 6. Checks
            temp_board = game.board.copy()
            temp_board.move_piece(from_pos, to_pos, promotion)
            opponent = 'black' if moving_piece.color == 'white' else 'white'
            if self._results_in_check(temp_board, opponent):
                score += 7000
            
            # 7. Central control and development (lower priority than tactical moves)
            central_squares = [(3,3), (3,4), (4,3), (4,4)]
            if to_pos in central_squares:
                score += 100
            
            # 8. Development in opening
            if game.move_count < 10 and isinstance(moving_piece, (Knight, Bishop)) and not moving_piece.has_moved:
                score += 500
            
            move_scores.append((score, (from_pos, to_pos, promotion)))
        
        # Sort by score in descending order
        move_scores.sort(reverse=True)
        return [move for _, move in move_scores]

    def _sort_tactical_moves(self, game, moves):
        """Sort tactical moves (captures, checks, promotions) for quiescence search"""
        move_scores = []
        
        for from_pos, to_pos, promotion in moves:
            score = 0
            moving_piece = game.board.get_piece(from_pos)
            target_piece = game.board.get_piece(to_pos)
            
            # 1. MVV-LVA for captures (Most Valuable Victim - Least Valuable Aggressor)
            if target_piece:
                target_value = self.piece_values.get(target_piece.__class__.__name__, 0)
                attacker_value = self.piece_values.get(moving_piece.__class__.__name__, 0)
                score = 10 * target_value - attacker_value
                
                # Winning captures (SEE)
                if self._is_favorable_capture(game.board, from_pos, to_pos):
                    score += 1000
            
            # 2. Promotions - very high value
            if promotion:
                promo_values = {'Q': 900, 'R': 500, 'B': 330, 'N': 320}
                score += 5000 + promo_values.get(promotion, 0)
                
            # 3. Checks in quiescence are valuable too
            temp_board = game.board.copy()
            temp_board.move_piece(from_pos, to_pos, promotion)
            opponent = 'black' if moving_piece.color == 'white' else 'white'
            if self._results_in_check(temp_board, opponent):
                score += 3000
                
            move_scores.append((score, (from_pos, to_pos, promotion)))
            
        move_scores.sort(reverse=True)
        return [move for _, move in move_scores]
        
    def _is_favorable_capture(self, board, from_pos, to_pos):
        """Basic Static Exchange Evaluation (SEE) to check if a capture is favorable"""
        moving_piece = board.get_piece(from_pos)
        target_piece = board.get_piece(to_pos)
        
        if not target_piece:
            return False
            
        moving_value = self.piece_values.get(moving_piece.__class__.__name__, 0)
        target_value = self.piece_values.get(target_piece.__class__.__name__, 0)
        
        # Simple evaluation: is the piece being captured more valuable?
        if target_value > moving_value:
            return True
            
        # Check if the capturing piece would be captured back
        # Temporarily make the capture
        temp_board = board.copy()
        temp_board.move_piece(from_pos, to_pos)
        
        # Now check if the target square is under attack
        opponent_color = 'black' if moving_piece.color == 'white' else 'white'
        if temp_board.is_under_attack(to_pos, opponent_color):
            # The capturing piece would be recaptured, so check the exchange value
            return target_value >= moving_value
            
        # No immediate recapture, so it's favorable
        return True
        
    def _get_move_key(self, from_pos, to_pos):
        """Create a unique key for a move to use in the history table"""
        return f"{from_pos[0]},{from_pos[1]}-{to_pos[0]},{to_pos[1]}"
        
    def _store_killer_move(self, move, ply):
        """Store a killer move at the given ply"""
        if move != self.killer_moves[ply][0]:
            self.killer_moves[ply][1] = self.killer_moves[ply][0]
            self.killer_moves[ply][0] = move
            
    def _is_killer_move(self, move, ply):
        """Check if a move is a killer move at the given ply"""
        return move == self.killer_moves[ply][0] or move == self.killer_moves[ply][1]
        
    def _is_capture(self, board, from_pos, to_pos):
        """Check if a move is a capture"""
        return board.get_piece(to_pos) is not None