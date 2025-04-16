import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, font
import os
import sys
from chess.pieces import Pawn, King
from chess.game import Game

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Master - Player vs. AI")
        self.root.resizable(False, False)
        self.root.configure(bg="#2E2E2E")
        
        # Define color schemes (inspired by chess.com and lichess.org)
        self.color_schemes = {
            "classic": {
                "light_square": "#F0D9B5",
                "dark_square": "#B58863",
                "selected": "#829769", 
                "valid_move": "#BACA2B",
                "last_move": "#AAD2E4",
                "check": "#E45F5F",
                "white_piece": "#FFFFFF",
                "black_piece": "#000000",
                "coordinates": "#B58863",
                "background": "#2E2E2E",
                "text": "#FFFFFF",
                "highlight_text": "#B58863"
            },
            "blue": {
                "light_square": "#EBF0F5",
                "dark_square": "#5B8FB9",
                "selected": "#7DBCE1", 
                "valid_move": "#93E9BE",
                "last_move": "#AAD2E4",
                "check": "#E86A6A",
                "white_piece": "#FFFFFF",
                "black_piece": "#000000",
                "coordinates": "#5B8FB9",
                "background": "#2A4C6D",
                "text": "#FFFFFF",
                "highlight_text": "#93E9BE"
            },
            "green": {
                "light_square": "#EEEED2",
                "dark_square": "#769656",
                "selected": "#BACA44", 
                "valid_move": "#F6F669",
                "last_move": "#AAD2E4",
                "check": "#C24949",
                "white_piece": "#FFFFFF",
                "black_piece": "#000000",
                "coordinates": "#769656",
                "background": "#3A5741",
                "text": "#FFFFFF",
                "highlight_text": "#BACA44"
            }
        }
        
        # Current color scheme
        self.current_scheme = "classic"
        self.colors = self.color_schemes[self.current_scheme]
        
        self.ai_color = 'black'
        self.ai_depth = 3
        self.game = Game(ai_opponent=True, ai_color=self.ai_color, ai_depth=self.ai_depth)
        self.selected_square = None
        self.last_move = None
        
        # Create custom styles for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.colors["background"])
        self.style.configure('TLabel', background=self.colors["background"], foreground=self.colors["text"])
        self.style.configure('TButton', background=self.colors["dark_square"], foreground=self.colors["text"], 
                            font=('Arial', 10, 'bold'), borderwidth=1)
        self.style.map('TButton', background=[('active', self.colors["selected"])])
        
        # Setup menu with modern styling
        menubar = tk.Menu(root, bg=self.colors["background"], fg=self.colors["text"], 
                         activebackground=self.colors["selected"], activeforeground=self.colors["text"],
                         relief=tk.FLAT, bd=0)
        
        gamemenu = tk.Menu(menubar, tearoff=0, bg=self.colors["background"], fg=self.colors["text"], 
                          activebackground=self.colors["selected"], activeforeground=self.colors["text"],
                          relief=tk.FLAT, bd=0)
        gamemenu.add_command(label="New Game", command=self.new_game)
        gamemenu.add_command(label="AI Settings", command=self.ai_settings)
        gamemenu.add_command(label="Undo Move", command=self.undo_move)
        gamemenu.add_command(label="Show Tactics", command=self.show_tactics)
        gamemenu.add_separator()
        
        # Add theme submenu
        theme_menu = tk.Menu(gamemenu, tearoff=0, bg=self.colors["background"], fg=self.colors["text"], 
                            activebackground=self.colors["selected"], activeforeground=self.colors["text"],
                            relief=tk.FLAT, bd=0)
        theme_menu.add_command(label="Classic", command=lambda: self.change_theme("classic"))
        theme_menu.add_command(label="Blue", command=lambda: self.change_theme("blue"))
        theme_menu.add_command(label="Green", command=lambda: self.change_theme("green"))
        gamemenu.add_cascade(label="Change Theme", menu=theme_menu)
        
        gamemenu.add_separator()
        gamemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="Game", menu=gamemenu)
        root.config(menu=menubar)
        
        # Create main frame with modern styling
        main_frame = ttk.Frame(root, style='TFrame')
        main_frame.pack(padx=20, pady=20)
        
        # Create a title/header
        header_frame = ttk.Frame(main_frame, style='TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        title_font = font.Font(family="Arial", size=18, weight="bold")
        title_label = ttk.Label(header_frame, text="Chess Master", font=title_font, 
                              foreground=self.colors["highlight_text"], style='TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Create board frame with a decorative border
        board_container = ttk.Frame(main_frame, style='TFrame')
        board_container.grid(row=1, column=0, padx=(0, 20), pady=5)
        
        self.board_frame = ttk.Frame(board_container, style='TFrame')
        self.board_frame.pack(padx=5, pady=5)
        
        # Info frame with game details
        info_frame = ttk.Frame(main_frame, style='TFrame')
        info_frame.grid(row=1, column=1, padx=5, pady=5, sticky="n")
        
        # Player info with improved styling
        player_frame = ttk.Frame(info_frame, style='TFrame')
        player_frame.pack(fill="x", pady=(0, 15))
        
        # White player display
        white_frame = ttk.Frame(player_frame, style='TFrame')
        white_frame.pack(fill="x", pady=2)
        white_label = ttk.Label(white_frame, text="White", font=("Arial", 12, "bold"), 
                             foreground=self.colors["white_piece"], style='TLabel')
        white_label.pack(side=tk.LEFT)
        white_indicator = tk.Frame(white_frame, width=12, height=12, bg=self.colors["background"])
        white_indicator.pack(side=tk.RIGHT, padx=5)
        self.white_indicator = white_indicator
        
        # Black player display
        black_frame = ttk.Frame(player_frame, style='TFrame')
        black_frame.pack(fill="x", pady=2)
        black_label = ttk.Label(black_frame, text="Black (AI)", font=("Arial", 12, "bold"), 
                             foreground=self.colors["text"], style='TLabel')
        black_label.pack(side=tk.LEFT)
        black_indicator = tk.Frame(black_frame, width=12, height=12, bg=self.colors["background"])
        black_indicator.pack(side=tk.RIGHT, padx=5)
        self.black_indicator = black_indicator
        
        # Status displays with improved styling
        status_frame = ttk.Frame(info_frame, style='TFrame')
        status_frame.pack(fill="x", pady=(0, 15))
        
        self.turn_label = ttk.Label(status_frame, text="White's turn", 
                                 font=("Arial", 14, "bold"), foreground=self.colors["highlight_text"],
                                 style='TLabel')
        self.turn_label.pack(anchor="w", pady=5)
        
        self.status_label = ttk.Label(status_frame, text="", font=("Arial", 12), style='TLabel')
        self.status_label.pack(anchor="w", pady=5)
        
        self.ai_label = ttk.Label(status_frame, 
                               text=f"AI: {self.ai_color.capitalize()} (Depth: {self.ai_depth})", 
                               font=("Arial", 12), style='TLabel')
        self.ai_label.pack(anchor="w", pady=5)
        
        # Action buttons with improved styling
        buttons_frame = ttk.Frame(info_frame, style='TFrame')
        buttons_frame.pack(fill="x", pady=(0, 15))
        
        new_game_btn = ttk.Button(buttons_frame, text="New Game", command=self.new_game)
        new_game_btn.pack(fill="x", pady=2)
        
        undo_btn = ttk.Button(buttons_frame, text="Undo Move", command=self.undo_move)
        undo_btn.pack(fill="x", pady=2)
        
        tactics_btn = ttk.Button(buttons_frame, text="Show Tactics", command=self.show_tactics)
        tactics_btn.pack(fill="x", pady=2)
        
        settings_btn = ttk.Button(buttons_frame, text="AI Settings", command=self.ai_settings)
        settings_btn.pack(fill="x", pady=2)
        
        quit_btn = ttk.Button(buttons_frame, text="Quit Game", command=self.root.quit)
        quit_btn.pack(fill="x", pady=2)
        
        # Move history with improved styling
        history_frame = ttk.LabelFrame(info_frame, text="Move History", 
                                    style='TLabel', padding=10)
        history_frame.pack(fill="both", expand=True, pady=5)
        
        history_scroll = ttk.Scrollbar(history_frame)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Custom styling for the listbox
        self.history_list = tk.Listbox(history_frame, width=20, height=15, font=("Arial", 10),
                                     bg=self.colors["background"], fg=self.colors["text"],
                                     selectbackground=self.colors["selected"], 
                                     selectforeground=self.colors["text"],
                                     relief=tk.FLAT, bd=1)
        self.history_list.pack(side=tk.LEFT, fill="both", expand=True)
        history_scroll.config(command=self.history_list.yview)
        self.history_list.config(yscrollcommand=history_scroll.set)
        
        # Initialize the squares for the board
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        
        # Create the chess board
        self.create_board()
        
        # Update board display
        self.update_board()
        
        # Set up the turn indicators
        self._update_turn_indicators()

    def _update_turn_indicators(self):
        """Update the turn indicators based on the current turn."""
        if self.game.turn == 'white':
            self.white_indicator.configure(bg=self.colors["selected"])
            self.black_indicator.configure(bg=self.colors["background"])
        else:
            self.white_indicator.configure(bg=self.colors["background"])
            self.black_indicator.configure(bg=self.colors["selected"])

    def create_board(self):
        """Create the chess board with improved styling."""
        # Configure the board grid
        for i in range(8):
            # Row labels (8-1)
            row_label = ttk.Label(self.board_frame, text=str(8-i), width=2, 
                               font=("Arial", 10), foreground=self.colors["coordinates"],
                               background=self.colors["background"], anchor="center")
            row_label.grid(row=i, column=0, padx=(0, 5))
            
            # Column labels (a-h)
            if i < 8:  # Only need 8 column labels
                col_label = ttk.Label(self.board_frame, text=chr(ord('a') + i), 
                                   font=("Arial", 10), foreground=self.colors["coordinates"],
                                   background=self.colors["background"], anchor="center")
                col_label.grid(row=8, column=i+1, pady=(5, 0))
        
        # Create the squares
        for row in range(8):
            for col in range(8):
                # Alternate colors for the chess board pattern
                color = self.colors["light_square"] if (row + col) % 2 == 0 else self.colors["dark_square"]
                
                # Create the square with a nicer appearance
                square = tk.Label(self.board_frame, bg=color, width=5, height=2, 
                                font=("Arial", 36, "bold"), bd=0, relief=tk.FLAT)
                square.grid(row=row, column=col+1)
                
                # Bind the click event
                square.bind("<Button-1>", lambda e, r=row, c=col: self.square_clicked(r, c))
                
                # Store the square reference
                self.squares[row][col] = square

    def update_board(self):
        """Update the chess board display with modern styling."""
        # Reset selection
        self.selected_square = None
        
        # Update each square
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                piece = self.game.board.grid[row][col]
                
                # Set the appropriate background color
                if self.last_move and (row, col) in [self.last_move[0], self.last_move[1]]:
                    # Highlight the last move squares
                    square.config(bg=self.colors["last_move"])
                else:
                    # Regular board pattern
                    square.config(bg=self.colors["light_square"] if (row + col) % 2 == 0 
                                 else self.colors["dark_square"])
                
                # Display the piece with appropriate color
                if piece:
                    symbol = {'King': '♚' if piece.color == 'black' else '♔', 
                             'Queen': '♛' if piece.color == 'black' else '♕', 
                             'Rook': '♜' if piece.color == 'black' else '♖', 
                             'Bishop': '♝' if piece.color == 'black' else '♗', 
                             'Knight': '♞' if piece.color == 'black' else '♘', 
                             'Pawn': '♟' if piece.color == 'black' else '♙'}.get(piece.__class__.__name__, '')
                    
                    square.config(text=symbol, 
                                 fg=self.colors["black_piece"] if piece.color == 'black' 
                                   else self.colors["white_piece"])
                else:
                    square.config(text="")
        
        # Update turn indicator
        self.turn_label.config(text=f"{self.game.turn.capitalize()}'s turn")
        
        # Update AI info
        self.ai_label.config(text=f"AI: {self.game.ai_color.capitalize()} (Depth: {self.game.ai.search_depth})")
        
        # Update turn indicators
        self._update_turn_indicators()
        
        # Check for game state and update status
        if self.game.in_checkmate(self.game.turn):
            winner = 'Black' if self.game.turn == 'white' else 'White'
            self.status_label.config(text=f"Checkmate! {winner} wins!")
            messagebox.showinfo("Game Over", f"Checkmate! {winner} wins!")
        elif self.game.in_stalemate(self.game.turn):
            self.status_label.config(text="Stalemate! Game ends in a draw.")
            messagebox.showinfo("Game Over", "Stalemate! Game ends in a draw.")
        elif self.game.in_check(self.game.turn):
            self.status_label.config(text=f"{self.game.turn.capitalize()} is in check!")
            
            # Highlight the king in check
            for r in range(8):
                for c in range(8):
                    piece = self.game.board.grid[r][c]
                    if piece and isinstance(piece, King) and piece.color == self.game.turn:
                        self.squares[r][c].config(bg=self.colors["check"])
                        break
        else:
            self.status_label.config(text="")

    def square_clicked(self, row, col):
        """Handle a click on a chess square with improved visual feedback."""
        # Don't allow moves when it's the AI's turn
        if self.game.turn == self.game.ai_color:
            return
        
        pos = (row, col)
        piece = self.game.board.get_piece(pos)
        
        # First click - select a piece
        if self.selected_square is None:
            if piece and piece.color == self.game.turn:
                # Select this piece
                self.selected_square = pos
                
                # Highlight the selected square
                self.squares[row][col].config(bg=self.colors["selected"])
                
                # Show valid moves
                legal_moves = piece.legal_moves(self.game.board)
                for move in legal_moves:
                    r, c = move
                    new_board = self.game.board.copy()
                    new_board.move_piece(pos, move)
                    
                    # Check if the move would not leave the king in check
                    if not Game._king_in_check_after_move(new_board, self.game.turn):
                        self.squares[r][c].config(bg=self.colors["valid_move"])
        
        # Second click - move the selected piece
        else:
            sel_row, sel_col = self.selected_square
            selected_piece = self.game.board.get_piece(self.selected_square)
            
            # Clicked on the same square - deselect
            if self.selected_square == pos:
                self.update_board()
                return
            
            # Clicked on another of player's pieces - change selection
            if piece and piece.color == self.game.turn:
                self.update_board()
                self.selected_square = pos
                self.squares[row][col].config(bg=self.colors["selected"])
                
                # Show valid moves for newly selected piece
                legal_moves = piece.legal_moves(self.game.board)
                for move in legal_moves:
                    r, c = move
                    new_board = self.game.board.copy()
                    new_board.move_piece(pos, move)
                    if not Game._king_in_check_after_move(new_board, self.game.turn):
                        self.squares[r][c].config(bg=self.colors["valid_move"])
                return
            
            # Clicked on a target square - attempt to move
            from_pos = self.selected_square
            to_pos = pos
            promotion_piece = None
            
            # Handle pawn promotion with a dialog
            if (isinstance(selected_piece, Pawn) and 
                ((selected_piece.color == 'white' and to_pos[0] == 0) or 
                 (selected_piece.color == 'black' and to_pos[0] == 7)) and 
                to_pos in selected_piece.legal_moves(self.game.board)):
                
                # Create a custom promotion dialog with piece symbols
                promotion_piece = self._show_promotion_dialog()
            
            # Try to make the move
            if self.try_move(from_pos, to_pos, promotion_piece):
                # Store the last move for highlighting
                self.last_move = (from_pos, to_pos)
                
                # Add to move history
                from_alg = self.pos_to_algebraic(from_pos)
                to_alg = self.pos_to_algebraic(to_pos)
                
                # Format move text with appropriate styling
                move_num = len(self.game.history) // 2 + (1 if self.game.turn == 'black' else 0)
                move_text = f"{move_num}. {from_alg} → {to_alg}"
                if promotion_piece:
                    # Show the promotion piece symbol
                    symbol = {'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞'}.get(promotion_piece, '♛')
                    move_text += f" = {symbol}"
                    
                self.history_list.insert(tk.END, move_text)
                self.history_list.see(tk.END)
                
                # Alternate colors in the move history list for better readability
                if self.history_list.size() % 2 == 0:
                    self.history_list.itemconfigure(tk.END, background=self.colors["dark_square"])
            
            # Update the board display
            self.update_board()
    
    def _show_promotion_dialog(self):
        """Display a custom promotion dialog with piece symbols."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Promote Pawn")
        dialog.configure(bg=self.colors["background"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Position dialog near the center of the main window
        dialog.geometry(f"+{self.root.winfo_rootx() + 150}+{self.root.winfo_rooty() + 150}")
        
        # Dialog message
        message = ttk.Label(dialog, text="Choose a piece for promotion:", 
                         font=("Arial", 12, "bold"), style='TLabel')
        message.pack(pady=(10, 20))
        
        # Store the result
        result = tk.StringVar(value="Q")
        
        # Create the piece selection buttons
        pieces_frame = ttk.Frame(dialog, style='TFrame')
        pieces_frame.pack(pady=(0, 20), padx=20, fill="x")
        
        # Queen button
        queen_btn = tk.Button(pieces_frame, text="♕", font=("Arial", 36), bg=self.colors["dark_square"],
                            fg=self.colors["white_piece"], relief=tk.FLAT, width=3, height=1)
        queen_btn.pack(side=tk.LEFT, padx=5)
        queen_btn.configure(command=lambda: [result.set("Q"), dialog.destroy()])
        
        # Rook button
        rook_btn = tk.Button(pieces_frame, text="♖", font=("Arial", 36), bg=self.colors["dark_square"],
                          fg=self.colors["white_piece"], relief=tk.FLAT, width=3, height=1)
        rook_btn.pack(side=tk.LEFT, padx=5)
        rook_btn.configure(command=lambda: [result.set("R"), dialog.destroy()])
        
        # Bishop button
        bishop_btn = tk.Button(pieces_frame, text="♗", font=("Arial", 36), bg=self.colors["dark_square"],
                            fg=self.colors["white_piece"], relief=tk.FLAT, width=3, height=1)
        bishop_btn.pack(side=tk.LEFT, padx=5)
        bishop_btn.configure(command=lambda: [result.set("B"), dialog.destroy()])
        
        # Knight button
        knight_btn = tk.Button(pieces_frame, text="♘", font=("Arial", 36), bg=self.colors["dark_square"],
                            fg=self.colors["white_piece"], relief=tk.FLAT, width=3, height=1)
        knight_btn.pack(side=tk.LEFT, padx=5)
        knight_btn.configure(command=lambda: [result.set("N"), dialog.destroy()])
        
        # Wait for the dialog to be closed
        self.root.wait_window(dialog)
        return result.get()

    def try_move(self, from_pos, to_pos, promotion_piece=None):
        """Attempt to make a move on the board."""
        if self.game.play_move(from_pos, to_pos, promotion_piece):
            # Flash the moved piece for visual feedback
            self.root.update()
            
            # If it's now the AI's turn, update after a short delay
            if self.game.turn == self.game.ai_color:
                self.root.after(500, self.update_board)
            
            return True
        return False

    def save_ai_settings(self, color, depth, dialog):
        """Save the new AI settings and optionally start a new game."""
        if color != self.ai_color or depth != self.ai_depth:
            # Store the new settings
            self.ai_color = color
            self.ai_depth = depth
            
            # Ask if the user wants to start a new game
            if messagebox.askyesno("New Game", 
                               "Start a new game with these AI settings?",
                               icon=messagebox.QUESTION):
                dialog.destroy()
                self.new_game()
            else:
                dialog.destroy()
                # Update existing game
                self.game.ai_color = self.ai_color
                self.game.ai.search_depth = self.ai_depth
                self.game.ai.color = self.ai_color
                self.game.ai.opponent_color = 'white' if self.ai_color == 'black' else 'black'
                self.update_board()
        else:
            dialog.destroy()

    def show_tactics(self):
        """Display identified tactical patterns on the board."""
        tactics = self.game.detect_tactics()
        
        # Clear previous board state and update
        self.update_board()
        
        if not any(tactics.values()):
            messagebox.showinfo("Tactics", "No tactical patterns detected on the board.",
                             icon=messagebox.INFO)
        else:
            # Highlight the tactical patterns on the board
            if tactics['pins']:
                for pin in tactics['pins']:
                    r, c = pin['position']
                    self.squares[r][c].config(bg="#E86A6A")  # Red for pins
            
            if tactics['forks']:
                for fork in tactics['forks']:
                    r, c = fork['position']
                    self.squares[r][c].config(bg="#6AE86A")  # Green for forks
                    for target in fork['targets']:
                        tr, tc = target['position']
                        self.squares[tr][tc].config(bg="#6AE86A")
            
            if tactics['skewers']:
                for skewer in tactics['skewers']:
                    r, c = skewer['position']
                    self.squares[r][c].config(bg="#6A6AE8")  # Blue for skewers
                    for target in skewer['targets']:
                        tr, tc = target['position']
                        self.squares[tr][tc].config(bg="#6A6AE8")
            
            # Create detailed text for the message box
            tactic_text = "Tactical Patterns:\n\n"
            
            if tactics['pins']:
                tactic_text += "Pins:\n" + "\n".join(
                    f"- {pin['piece'].__class__.__name__} at {pin['algebraic']} is pinned" 
                    for pin in tactics['pins']) + "\n\n"
            
            if tactics['forks']:
                tactic_text += "Forks:\n" + "\n".join(
                    f"- {fork['attacker'].__class__.__name__} at {fork['algebraic']} is forking "
                    f"{' and '.join(t['piece'].__class__.__name__ + ' at ' + t['algebraic'] for t in fork['targets'])}" 
                    for fork in tactics['forks']) + "\n\n"
            
            if tactics['skewers']:
                tactic_text += "Skewers:\n" + "\n".join(
                    f"- {skewer['attacker'].__class__.__name__} at {skewer['algebraic']} is skewering "
                    f"{' and '.join(t['piece'].__class__.__name__ + ' at ' + t['algebraic'] for t in skewer['targets'])}" 
                    for skewer in tactics['skewers'])
            
            # Show the detailed description
            messagebox.showinfo("Tactics", tactic_text, icon=messagebox.INFO)
            
            # Schedule to clear the highlights after a delay
            self.root.after(5000, self.update_board)

    def pos_to_algebraic(self, pos):
        """Convert board position to algebraic notation."""
        row, col = pos
        return chr(ord('a') + col) + str(8 - row)

    def change_theme(self, theme_name):
        """Change the color theme of the GUI."""
        if theme_name in self.color_schemes:
            self.current_scheme = theme_name
            self.colors = self.color_schemes[theme_name]
            
            # Update root background
            self.root.configure(bg=self.colors["background"])
            
            # Update ttk styles
            self.style.configure('TFrame', background=self.colors["background"])
            self.style.configure('TLabel', background=self.colors["background"], foreground=self.colors["text"])
            self.style.configure('TButton', background=self.colors["dark_square"], foreground=self.colors["text"])
            self.style.map('TButton', background=[('active', self.colors["selected"])])
            
            # Update listbox colors
            self.history_list.configure(
                bg=self.colors["background"], 
                fg=self.colors["text"],
                selectbackground=self.colors["selected"], 
                selectforeground=self.colors["text"]
            )
            
            # Redraw the board with new colors
            self.update_board()
            
            # Update turn indicators
            self._update_turn_indicators()

    def new_game(self):
        """Start a new game with confirmation."""
        if messagebox.askyesno("New Game", "Start a new game?", 
                           icon=messagebox.QUESTION):
            # Reset the game
            self.game = Game(ai_opponent=True, ai_color=self.ai_color, ai_depth=self.ai_depth)
            self.last_move = None
            
            # Clear history
            self.history_list.delete(0, tk.END)
            
            # Update the board
            self.update_board()
            
            # If AI plays white, make its move
            if self.ai_color == 'white':
                self.root.after(500, self.game.make_ai_move)
                self.root.after(600, self.update_board)

    def undo_move(self):
        """Undo the last player and AI moves."""
        # Need at least 2 moves to undo (player + AI)
        if self.game.ai_opponent and len(self.game.history) >= 2:
            # Undo AI's move
            self.game.undo_move()
            # Undo player's move
            self.game.undo_move()
            
            # Clear the last move highlight
            if len(self.game.history) > 0:
                self.last_move = (self.game.history[-1][0], self.game.history[-1][1])
            else:
                self.last_move = None
            
            # Update the board
            self.update_board()
            
            # Remove the last two moves from history display
            if self.history_list.size() > 0:
                self.history_list.delete(self.history_list.size()-1)
            if self.history_list.size() > 0:
                self.history_list.delete(self.history_list.size()-1)

    def ai_settings(self):
        """Show dialog to configure the AI settings."""
        # Create a themed dialog
        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.title("AI Settings")
        settings_dialog.configure(bg=self.colors["background"])
        settings_dialog.geometry("350x220")
        settings_dialog.transient(self.root)
        settings_dialog.grab_set()
        
        # Title label
        title_label = ttk.Label(settings_dialog, text="AI Configuration", 
                             font=("Arial", 14, "bold"), 
                             foreground=self.colors["highlight_text"], style='TLabel')
        title_label.pack(pady=(15, 25))
        
        # AI color selection
        color_frame = ttk.Frame(settings_dialog, style='TFrame')
        color_frame.pack(fill="x", padx=30, pady=5)
        
        color_label = ttk.Label(color_frame, text="AI plays as:", 
                             font=("Arial", 12), style='TLabel')
        color_label.pack(side=tk.LEFT, padx=5)
        
        color_var = tk.StringVar(value=self.ai_color)
        
        # Custom styled radio buttons
        white_rb = ttk.Radiobutton(color_frame, text="White", variable=color_var, 
                                value="white", style='TLabel')
        white_rb.pack(side=tk.LEFT, padx=15)
        
        black_rb = ttk.Radiobutton(color_frame, text="Black", variable=color_var, 
                                value="black", style='TLabel')
        black_rb.pack(side=tk.LEFT, padx=15)
        
        # AI difficulty selection
        difficulty_frame = ttk.Frame(settings_dialog, style='TFrame')
        difficulty_frame.pack(fill="x", padx=30, pady=15)
        
        difficulty_label = ttk.Label(difficulty_frame, text="Difficulty:", 
                                  font=("Arial", 12), style='TLabel')
        difficulty_label.pack(side=tk.LEFT, padx=5)
        
        depth_var = tk.IntVar(value=self.ai_depth)
        
        # Modern horizontal slider
        difficulty_scale = ttk.Scale(difficulty_frame, from_=1, to=5, orient=tk.HORIZONTAL,
                                 variable=depth_var, length=150)
        difficulty_scale.pack(side=tk.LEFT, padx=15)
        
        # Add a label to show the current value
        depth_label = ttk.Label(difficulty_frame, text=str(self.ai_depth), 
                             font=("Arial", 12, "bold"), width=2, style='TLabel')
        depth_label.pack(side=tk.LEFT, padx=5)
        
        # Update the label when the scale changes
        def update_depth_label(event=None):
            depth_label.config(text=str(int(depth_var.get())))
        
        difficulty_scale.bind("<Motion>", update_depth_label)
        difficulty_scale.bind("<ButtonRelease-1>", update_depth_label)
        
        # Button frame
        button_frame = ttk.Frame(settings_dialog, style='TFrame')
        button_frame.pack(pady=20)
        
        # Save button with custom style
        save_btn = ttk.Button(button_frame, text="Save", width=10,
                           command=lambda: self.save_ai_settings(
                               color_var.get(), int(depth_var.get()), settings_dialog))
        save_btn.pack(side=tk.LEFT, padx=10)
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="Cancel", width=10,
                             command=settings_dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)