import re
import streamlit as st
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.model.google import Gemini

# Streamlit App Title
st.title("🎮 Tic-Tac-Toe: AI vs AI")

# Enhanced Welcome Message
st.markdown("""
    **Welcome to the Ultimate Tic-Tac-Toe Game!** 🎮  
    Watch two advanced AI agents battle it out in a game of Tic-Tac-Toe.  
    Here's what you need to know:
""")
st.info("""
    - **Player X**: AI (Gemini).  
    - **Player O**: AI (OpenAI).  
    - **Goal**: The first player to get three of their symbols in a row (horizontally, vertically, or diagonally) wins.  
    - **Draw**: If the board fills up without a winner, the game ends in a draw.  
""")
st.markdown("Ready to play? Click the **Start Game** button below! 🚀")

# Initialize the game board in session state
if 'board' not in st.session_state:
    st.session_state.board = [[None, None, None],
                              [None, None, None],
                              [None, None, None]]

# Function to display the board with better styling
def display_board(board):
    st.markdown("""
        <style>
        .board {
            display: grid;
            grid-template-columns: repeat(3, 100px);
            grid-template-rows: repeat(3, 100px);
            gap: 5px;
            margin-bottom: 20px;
        }
        .cell {
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #4a4a4a;
            font-size: 24px;
            font-weight: bold;
            background-color: #f0f0f0;
            border-radius: 10px;
        }
        .cell.X {
            color: #FF0000; /* Red color for X */
        }
        .cell.O {
            color: #0000FF; /* Blue color for O */
        }
        </style>
    """, unsafe_allow_html=True)

    st.write("### Current Board")
    board_html = '<div class="board">'
    for row in board:
        for cell in row:
            cell_value = cell if cell is not None else "&nbsp;"
            cell_class = f"cell {cell}" if cell in ["X", "O"] else "cell"
            board_html += f'<div class="{cell_class}">{cell_value}</div>'
    board_html += '</div>'
    st.markdown(board_html, unsafe_allow_html=True)

# Function to get the board state as a string
def get_board_state(board):
    rows = []
    for i, row in enumerate(board):
        row_str = " | ".join([f"({i},{j}) {cell or ' '}" for j, cell in enumerate(row)])
        rows.append(f"Row {i}: {row_str}")
    return "\n".join(rows)

# Function to check for a winner
def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] and row[0] is not None:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] is not None:
            return board[0][col]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
        return board[0][2]
    # Check for draw
    if all(cell is not None for row in board for cell in row):
        return "Draw"
    return None

# Sidebar for API keys
st.sidebar.header("🔑 API Keys")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
google_api_key = st.sidebar.text_input("Google API Key (for Gemini)", type="password")

if openai_api_key:
    st.session_state.openai_api_key = openai_api_key
if google_api_key:
    st.session_state.google_api_key = google_api_key

# Initialize agents if API keys are provided
if 'openai_api_key' in st.session_state and 'google_api_key' in st.session_state:
    player_x = Agent(
        name="Player X (Gemini)",
        model=Gemini(id="gemini-2.0-flash", api_key=st.session_state.google_api_key),
        instructions=[
            "You are a Tic-Tac-Toe player using the symbol 'X'.",
            "Your opponent is using the symbol 'O'. Block their potential winning moves.",
            "Make your move in the format 'row, col' based on the current board state.",
            "Strategize to win by placing your symbol in a way that blocks your opponent from forming a straight line.",
            "Do not include any explanations or extra text. Only provide the move.",
            "Row and column indices start from 0.",
        ],
        markdown=True,
    )

    player_o = Agent(
        name="Player O (OpenAI)",
        model=OpenAIChat(id="gpt-4o", temperature=0.1, api_key=st.session_state.openai_api_key),
        instructions=[
            "You are a Tic-Tac-Toe player using the symbol 'O'.",
            "Your opponent is using the symbol 'X'. Block their potential winning moves.",
            "Make your move in the format 'row, col' based on the current board state.",
            "Strategize to win by placing your symbol in a way that blocks your opponent from forming a straight line.",
            "Do not include any explanations or extra text. Only provide the move.",
            "Row and column indices start from 0.",
        ],
        markdown=True,
    )

    judge = Agent(
        name="Judge",
        model=OpenAIChat(id="gpt-4", temperature=0.1, api_key=st.session_state.openai_api_key),
        instructions=[
            "You are the judge of a Tic-Tac-Toe game.",
            "The board is presented as rows with positions separated by '|'.",
            "Rows are labeled from 0 to 2, and columns from 0 to 2.",
            "Determine the winner based on this board state.",
            "The winner is the player with three of their symbols in a straight line (row, column, or diagonal).",
            "If the board is full and there is no winner, declare a draw.",
            "Provide only the result (e.g., 'Player X wins', 'Player O wins', 'Draw').",
        ],
        markdown=True,
    )

    # Function to extract the move from the agent's response
    def extract_move(response):
        content = response.content.strip()
        match = re.search(r'\d\s*,\s*\d', content)
        if match:
            return match.group().replace(' ', '')
        numbers = re.findall(r'\d+', content)
        if len(numbers) >= 2:
            return f"{numbers[0]},{numbers[1]}"
        return None

    # Game loop
    def play_game():
        if 'current_player' not in st.session_state:
            st.session_state.current_player = player_x
        if 'symbol' not in st.session_state:
            st.session_state.symbol = "X"
        if 'move_count' not in st.session_state:
            st.session_state.move_count = 0

        max_moves = 9
        winner = None

        while st.session_state.move_count < max_moves:
            display_board(st.session_state.board)

            # Prepare the board state for the agent
            board_state = get_board_state(st.session_state.board)
            move_prompt = (
                f"Current board state:\n{board_state}\n"
                f"{st.session_state.current_player.name}'s turn. Make your move in the format 'row, col'."
            )

            # Get the current player's move
            with st.chat_message("assistant"):
                st.write(f"**{st.session_state.current_player.name}'s turn:**")
                move_response = st.session_state.current_player.run(move_prompt)
                st.code(f"Agent {st.session_state.current_player.name} response:\n{move_response.content}", language="markdown")
                move = extract_move(move_response)
                st.write(f"**Extracted move:** {move}")

            if move is None:
                st.error("Invalid move! Please use the format 'row, col'.")
                continue

            try:
                row, col = map(int, move.split(','))
                if st.session_state.board[row][col] is not None:
                    st.error("Invalid move! Cell already occupied.")
                    continue
                st.session_state.board[row][col] = st.session_state.symbol
            except (ValueError, IndexError):
                st.error("Invalid move! Please use the format 'row, col'.")
                continue

            # Check for a winner or draw
            winner = check_winner(st.session_state.board)
            if winner:
                break

            # Switch players
            st.session_state.current_player = player_o if st.session_state.current_player == player_x else player_x
            st.session_state.symbol = "O" if st.session_state.symbol == "X" else "X"
            st.session_state.move_count += 1

        # Display final board and result
        st.write("### Final Board")
        display_board(st.session_state.board)

        if winner:
            st.success(f"**Result:** {winner}")
        else:
            st.success("**Result:** Draw")

        # Judge's announcement
        st.write("\n**Game Over. Judge is determining the result...**")
        st.write("**Final board state passed to judge:**")
        st.code(get_board_state(st.session_state.board), language="markdown")
        judge_prompt = (
            f"Final board state:\n{get_board_state(st.session_state.board)}\n"
            f"Determine the winner and announce the result."
        )
        judge_response = judge.run(judge_prompt)
        st.code(f"Judge's raw response:\n{judge_response.content}", language="markdown")
        announcement = judge_response.content.strip()
        st.success(f"**Judge's Announcement:** {announcement}")

    # Start Game Button
    if st.button("Start Game"):
        st.session_state.board = [[None, None, None],
                                  [None, None, None],
                                  [None, None, None]]
        st.session_state.current_player = player_x
        st.session_state.symbol = "X"
        st.session_state.move_count = 0
        play_game()

    # Play Again Button
    if st.button("Refresh"):
       st.session_state.board = [[None, None, None],
                                 [None, None, None],
                                 [None, None, None]]
       st.session_state.current_player = player_x
       st.session_state.symbol = "X"
       st.session_state.move_count = 0
       st.rerun()  # Refresh the app to start a new game
else:
    st.warning("Please enter your OpenAI API key and Google API key to start the game.")
