from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import math
app = Flask(__name__)
CORS(app)

SIZE = 19  # Kích thước bàn cờ
ai_score = 0  # Điểm của AI
opponent_score = 0  # Điểm của đối thủ

def get_neighbors(x, y):
    """Lấy danh sách các ô lân cận trên bàn cờ."""
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return [(x + dx, y + dy) for dx, dy in directions if 0 <= x + dx < SIZE and 0 <= y + dy < SIZE]

def has_liberty(board, x, y, player):
    """Kiểm tra xem quân cờ mới đặt có khí không (chỗ thở)."""
    stack = [(x, y)]
    visited = set()
    
    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))

        for nx, ny in get_neighbors(cx, cy):
            if board[nx][ny] == 0:  # Có khí
                return True
            elif board[nx][ny] == player and (nx, ny) not in visited:
                stack.append((nx, ny))
    
    return False  # Không còn khí, là nước đi không hợp lệ

def is_captured(board, x, y, visited):
    """Kiểm tra xem nhóm quân có bị bắt không."""
    stack = [(x, y)]
    color = board[x][y]
    group = []
    has_liberty = False

    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))
        group.append((cx, cy))

        for nx, ny in get_neighbors(cx, cy):
            if board[nx][ny] == 0:
                has_liberty = True
            elif board[nx][ny] == color and (nx, ny) not in visited:
                stack.append((nx, ny))

    return group if not has_liberty else []

def remove_captured_stones(board, player):
    """Xóa quân bị bắt khỏi bàn cờ và cập nhật điểm."""
    global ai_score, opponent_score
    opponent = 3 - player
    visited = set()
    captured_stones = []

    for x in range(SIZE):
        for y in range(SIZE):
            if board[x][y] == opponent and (x, y) not in visited:
                captured = is_captured(board, x, y, visited)
                if captured:
                    captured_stones.extend(captured)

    for x, y in captured_stones:
        board[x][y] = 0

    if player == 2:
        ai_score += len(captured_stones)
    else:
        opponent_score += len(captured_stones)

    return captured_stones

def find_closest_friendly_move(board, valid_moves, player):
    """Tìm nước đi hợp lệ gần nhất với quân đồng minh."""
    allies = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == player]

    if not allies or not valid_moves:
        return None  # Không có quân nào hoặc không có nước đi hợp lệ

    best_move = None
    min_distance = float("inf")

    for move in valid_moves:
        move_x, move_y = move
        for ally_x, ally_y in allies:
            distance = math.sqrt((move_x - ally_x) ** 2 + (move_y - ally_y) ** 2)
            if distance < min_distance:
                min_distance = distance
                best_move = move

    return best_move

# AI chọn nước đi

@app.route("/ai-move", methods=["POST"])
def ai_move():
    global ai_score, opponent_score
    data = request.get_json()
    board = data["board"]

    # Tìm các nước đi hợp lệ (ô trống)
    valid_moves = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    if not valid_moves:
        return jsonify({"error": "No valid moves"})

    best_move = None
    max_captured = 0
    safe_moves = []  # Danh sách nước đi có khí

    # Thử đặt quân và kiểm tra nước đi tốt nhất (ưu tiên bắt quân)
    for r, c in valid_moves:
        board_copy = [row[:] for row in board]  # Sao chép bàn cờ
        board_copy[r][c] = 2  # Đặt thử quân AI

        # Kiểm tra nếu nước đi này có khí
        if has_liberty_after_move(board_copy, r, c, 2):
            safe_moves.append((r, c))

            captured = remove_captured_stones(board_copy, 2)
            if len(captured) > max_captured:
                max_captured = len(captured)
                best_move = (r, c)

    # Nếu có nước đi bắt nhiều quân và vẫn có khí, chọn nước đó
    if best_move:
        ai_y, ai_x = best_move
    else:
        # Nếu không có nước đi nào bắt quân, chọn nước đi gần quân đồng minh nhưng vẫn có khí
        if safe_moves:
            ai_y, ai_x = find_closest_friendly_move(board, safe_moves, 2)
        else:
            return jsonify({"error": "No valid moves with liberty"})

    board[ai_y][ai_x] = 2  # Đặt quân AI lên bàn cờ
    captured = remove_captured_stones(board, 2)  # Kiểm tra và xóa quân bị bắt

    return jsonify({
        "ai_x": ai_x,
        "ai_y": ai_y,
        "ai_score": ai_score,
        "opponent_score": opponent_score,
        "captured_stones": captured  # Gửi danh sách quân bị bắt về client
    })


def has_liberty_after_move(board, x, y, player):
    """Kiểm tra xem nước đi (x, y) có khí sau khi đặt quân hay không."""
    visited = set()
    return len(is_captured(board, x, y, visited)) == 0

if __name__ == "__main__":
    app.run(debug=True)
