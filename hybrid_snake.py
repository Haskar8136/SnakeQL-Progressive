import numpy as np
import random
import pickle
import os
from collections import deque
import math
import time

class HybridSnakeAI:
    """
    Complete Hybrid Algorithm - WITH SIZE DETECTION
    - Automatically detects board size
    - Saves size together with the model
    - When loading, checks if size matches
    - If not matching, resets Q-Table but keeps hyperparameters
    """
    
    def __init__(self, grid_width=20, grid_height=15):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.total_cells = grid_width * grid_height
        
        # ========== MOVEMENT CONFIGURATION ==========
        self.strategies = ['AGGRESSIVE', 'BALANCED', 'SAFE', 'EXPLORE']
        
        self.maneuvers = {
            'AGGRESSIVE': ['TOWARD_FOOD', 'DIAGONAL_CUT', 'RISKY_SHORTCUT'],
            'BALANCED': ['FOLLOW_WALL', 'CIRCLE_AROUND', 'SAFE_APPROACH'],
            'SAFE': ['FOLLOW_TAIL', 'STAY_OPEN', 'AVOID_HEAD'],
            'EXPLORE': ['RANDOM', 'EXPLORE_UNSEEN', 'BORDER_FOLLOW']
        }
        
        self.all_actions = []
        for strategy in self.strategies:
            for maneuver in self.maneuvers[strategy]:
                self.all_actions.append(f"{strategy}|{maneuver}")
        
        # ========== Q-LEARNING PARAMETERS ==========
        self.learning_rate = 0.15
        self.discount_factor = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995
        
        self.q_table = {}
        
        # ========== INACTIVITY CONTROL ==========
        self.last_position = None
        self.stuck_counter = 0
        self.max_stuck_time = 3
        self.last_move_time = None
        
        # ========== ADDITIONAL PROTECTIONS ==========
        self.consecutive_safe_moves = 0
        self.starvation_counter = 0
        self.max_starvation = self.total_cells
        
        # ========== STATISTICS ==========
        self.episode_count = 0
        self.action_stats = {action: 0 for action in self.all_actions}
        
        print(f"✅ Hybrid Snake AI - Adapted to {grid_width}x{grid_height}")
        print(f"🎮 Strategies: {len(self.strategies)}")
        print(f"🎯 Total maneuvers: {len(self.all_actions)}")
        print(f"📐 Total cells: {self.total_cells}")
    
    def get_state(self, snake, food):
        """COMPLETE STATE - NORMALIZED for any board size"""
        if not snake:
            return None
        
        head = snake[0]
        head_x, head_y = head
        food_x, food_y = food
        
        # 1. Food direction (8 directions)
        dx = food_x - head_x
        dy = food_y - head_y
        
        if dx == 0 and dy == 0:
            food_dir = 0
        else:
            angle = math.atan2(dy, dx)
            food_dir = int((angle + math.pi) / (math.pi / 4)) % 8
        
        # 2. Normalized distance to food (4 levels)
        distance = abs(dx) + abs(dy)
        max_dist = self.grid_width + self.grid_height
        dist_level = min(3, int((distance / max_dist) * 4))
        
        # 3. Immediate danger
        danger_up = 1 if self.is_dangerous(snake, head_x, head_y - 1) else 0
        danger_down = 1 if self.is_dangerous(snake, head_x, head_y + 1) else 0
        danger_left = 1 if self.is_dangerous(snake, head_x - 1, head_y) else 0
        danger_right = 1 if self.is_dangerous(snake, head_x + 1, head_y) else 0
        danger_code = (danger_up << 3) | (danger_down << 2) | (danger_left << 1) | danger_right
        
        # 4. Normalized snake length
        snake_len = len(snake)
        len_level = min(3, int((snake_len / self.total_cells) * 4))
        
        # 5. Normalized free space
        free_space = self.count_accessible_space(head, set(snake[1:]))
        space_level = min(3, int((free_space / self.total_cells) * 4))
        
        # 6. Food in safe area
        food_safe = 1 if not self.is_dangerous(snake, food_x, food_y) else 0
        
        # 7. Path to food exists
        path_exists = 1 if self.has_path_to_food(snake, food) else 0
        
        # 8. Tail direction
        if len(snake) > 1:
            tail = snake[-1]
            tail_dir_x = tail[0] - snake[-2][0]
            tail_dir_y = tail[1] - snake[-2][1]
            if tail_dir_x > 0:
                tail_dir = 3
            elif tail_dir_x < 0:
                tail_dir = 2
            elif tail_dir_y > 0:
                tail_dir = 1
            else:
                tail_dir = 0
        else:
            tail_dir = 0
        
        state = (food_dir, dist_level, danger_code, len_level, space_level, food_safe, path_exists, tail_dir)
        return state
    
    def is_dangerous(self, snake, x, y):
        if x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height:
            return True
        if (x, y) in snake[1:]:
            return True
        return False
    
    def is_valid_move(self, snake, dx, dy):
        if not snake:
            return False
        
        head = snake[0]
        new_x = head[0] + dx
        new_y = head[1] + dy
        
        if new_x < 0 or new_x >= self.grid_width or new_y < 0 or new_y >= self.grid_height:
            return False
        
        new_head = (new_x, new_y)
        if new_head in snake[1:]:
            if new_head == snake[-1] and len(snake) > 1:
                return True
            return False
        
        return True
    
    def has_path_to_food(self, snake, food):
        if not snake:
            return False
        
        head = snake[0]
        obstacles = set(snake[1:])
        
        queue = deque([head])
        visited = {head}
        
        while queue:
            pos = queue.popleft()
            if pos == food:
                return True
            
            x, y = pos
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height and
                    (nx, ny) not in obstacles and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False
    
    def get_safe_moves(self, snake):
        if not snake:
            return []
        
        head = snake[0]
        safe_moves = []
        
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = head[0] + dx, head[1] + dy
            if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height and
                (nx, ny) not in snake[1:]):
                safe_moves.append((dx, dy))
        
        return safe_moves
    
    def count_accessible_space(self, start, obstacles):
        visited = set()
        queue = deque([start])
        count = 0
        max_count = min(200, self.total_cells)
        
        while queue and count < max_count:
            pos = queue.popleft()
            if pos in visited:
                continue
            visited.add(pos)
            count += 1
            
            x, y = pos
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height and
                    (nx, ny) not in obstacles and (nx, ny) not in visited):
                    queue.append((nx, ny))
        
        return count
    
    def execute_action(self, action, snake, food):
        if not snake:
            return (0, 0)
        
        strategy, maneuver = action.split('|')
        head = snake[0]
        head_x, head_y = head
        
        safe_moves = self.get_safe_moves(snake)
        if not safe_moves:
            return (0, 0)
        
        # AGGRESSIVE STRATEGY
        if strategy == 'AGGRESSIVE':
            if maneuver == 'TOWARD_FOOD':
                dx = np.sign(food[0] - head_x)
                dy = np.sign(food[1] - head_y)
                if dx != 0 and dy != 0:
                    if self.is_valid_move(snake, dx, 0):
                        return (dx, 0)
                    elif self.is_valid_move(snake, 0, dy):
                        return (0, dy)
                if dx != 0 and self.is_valid_move(snake, dx, 0):
                    return (dx, 0)
                if dy != 0 and self.is_valid_move(snake, 0, dy):
                    return (0, dy)
            
            elif maneuver == 'DIAGONAL_CUT':
                dx = np.sign(food[0] - head_x)
                dy = np.sign(food[1] - head_y)
                if self.is_valid_move(snake, dx, dy):
                    return (dx, dy)
                if safe_moves:
                    return random.choice(safe_moves)
            
            elif maneuver == 'RISKY_SHORTCUT':
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    if self.is_valid_move(snake, dx, dy):
                        return (dx, dy)
        
        # BALANCED STRATEGY
        elif strategy == 'BALANCED':
            if maneuver == 'FOLLOW_WALL':
                best_move = None
                best_score = -1
                for dx, dy in safe_moves:
                    nx, ny = head_x + dx, head_y + dy
                    dist_to_wall = min(nx, self.grid_width - 1 - nx, ny, self.grid_height - 1 - ny)
                    if dist_to_wall > best_score:
                        best_score = dist_to_wall
                        best_move = (dx, dy)
                if best_move:
                    return best_move
            
            elif maneuver == 'CIRCLE_AROUND':
                angle = math.atan2(food[1] - head_y, food[0] - head_x)
                angle += math.pi / 4
                dx = int(np.sign(math.cos(angle)))
                dy = int(np.sign(math.sin(angle)))
                if dx == 0 and dy == 0:
                    dx, dy = 1, 0
                if self.is_valid_move(snake, dx, dy):
                    return (dx, dy)
            
            elif maneuver == 'SAFE_APPROACH':
                best_move = None
                best_score = -float('inf')
                for dx, dy in safe_moves:
                    nx, ny = head_x + dx, head_y + dy
                    space = self.count_accessible_space((nx, ny), set(snake[1:]))
                    dist_to_food = abs(nx - food[0]) + abs(ny - food[1])
                    score = space - dist_to_food * 2
                    if score > best_score:
                        best_score = score
                        best_move = (dx, dy)
                if best_move:
                    return best_move
        
        # SAFE STRATEGY
        elif strategy == 'SAFE':
            if maneuver == 'FOLLOW_TAIL':
                if len(snake) > 1:
                    tail = snake[-1]
                    dx = np.sign(tail[0] - head_x)
                    dy = np.sign(tail[1] - head_y)
                    if dx != 0 and dy != 0:
                        if self.is_valid_move(snake, dx, 0):
                            return (dx, 0)
                        elif self.is_valid_move(snake, 0, dy):
                            return (0, dy)
                    if self.is_valid_move(snake, dx, dy):
                        return (dx, dy)
            
            elif maneuver == 'STAY_OPEN':
                best_move = None
                max_space = -1
                for dx, dy in safe_moves:
                    nx, ny = head_x + dx, head_y + dy
                    space = self.count_accessible_space((nx, ny), set(snake[1:]))
                    if space > max_space:
                        max_space = space
                        best_move = (dx, dy)
                if best_move:
                    return best_move
            
            elif maneuver == 'AVOID_HEAD':
                if safe_moves:
                    return safe_moves[0]
        
        # EXPLORE STRATEGY
        elif strategy == 'EXPLORE':
            if maneuver == 'RANDOM':
                if safe_moves:
                    return random.choice(safe_moves)
            
            elif maneuver == 'EXPLORE_UNSEEN':
                corners = [(0, 0), (0, self.grid_height-1), (self.grid_width-1, 0), (self.grid_width-1, self.grid_height-1)]
                farthest_corner = max(corners, key=lambda c: abs(c[0]-head_x) + abs(c[1]-head_y))
                dx = np.sign(farthest_corner[0] - head_x)
                dy = np.sign(farthest_corner[1] - head_y)
                if self.is_valid_move(snake, dx, dy):
                    return (dx, dy)
            
            elif maneuver == 'BORDER_FOLLOW':
                if head_x == 0 and self.is_valid_move(snake, 0, 1):
                    return (0, 1)
                elif head_x == self.grid_width - 1 and self.is_valid_move(snake, 0, -1):
                    return (0, -1)
                elif head_y == 0 and self.is_valid_move(snake, 1, 0):
                    return (1, 0)
                elif head_y == self.grid_height - 1 and self.is_valid_move(snake, -1, 0):
                    return (-1, 0)
        
        if safe_moves:
            return safe_moves[0]
        
        return (0, 0)
    
    def get_safe_move(self, snake):
        safe_moves = self.get_safe_moves(snake)
        if safe_moves:
            return safe_moves[0]
        return (0, 0)
    
    def check_stuck_penalty(self, snake):
        current_pos = snake[0] if snake else None
        
        if self.last_position == current_pos:
            if self.last_move_time is None:
                self.last_move_time = time.time()
            else:
                stuck_duration = time.time() - self.last_move_time
                if stuck_duration >= self.max_stuck_time:
                    self.stuck_counter += 1
                    self.last_move_time = time.time()
                    return -20
        else:
            self.last_position = current_pos
            self.last_move_time = None
            self.stuck_counter = 0
        
        return 0
    
    def choose_action(self, state, snake, food):
        if state not in self.q_table:
            self.q_table[state] = {action: 0 for action in self.all_actions}
        
        if random.random() < self.epsilon:
            action = random.choice(self.all_actions)
        else:
            action = max(self.all_actions, key=lambda a: self.q_table[state][a])
        
        self.action_stats[action] += 1
        return action
    
    def get_reward(self, snake, old_snake, food, ate, died, action, stuck_penalty):
        if died:
            return -100
        
        if ate:
            self.starvation_counter = 0
            strategy = action.split('|')[0]
            if strategy == 'AGGRESSIVE':
                return 60
            elif strategy == 'BALANCED':
                return 55
            else:
                return 50
        
        reward = -0.1
        reward += stuck_penalty
        
        self.starvation_counter += 1
        if self.starvation_counter > self.max_starvation // 2:
            reward -= 5
        if self.starvation_counter > self.max_starvation:
            reward -= 20
        
        if old_snake and snake:
            old_head = old_snake[0]
            new_head = snake[0]
            old_dist = abs(old_head[0] - food[0]) + abs(old_head[1] - food[1])
            new_dist = abs(new_head[0] - food[0]) + abs(new_head[1] - food[1])
            
            if new_dist < old_dist:
                reward += 3
            elif new_dist > old_dist:
                reward -= 2
        
        if self.epsilon > 0.5:
            strategy = action.split('|')[0]
            if strategy == 'EXPLORE':
                reward += 1
        
        return reward
    
    def update_q_table(self, state, action, reward, next_state, done):
        if state not in self.q_table:
            self.q_table[state] = {a: 0 for a in self.all_actions}
        
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0 for a in self.all_actions}
        
        current_q = self.q_table[state][action]
        
        if done:
            max_future_q = 0
        else:
            max_future_q = max(self.q_table[next_state].values())
        
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)
        self.q_table[state][action] = new_q
    
    def decay_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            self.epsilon = max(self.epsilon, self.epsilon_min)
    
    def get_action(self, snake, food):
        if not snake:
            return (0, 0)
        
        state = self.get_state(snake, food)
        action = self.choose_action(state, snake, food)
        dx, dy = self.execute_action(action, snake, food)
        
        if not self.is_valid_move(snake, dx, dy):
            safe_moves = self.get_safe_moves(snake)
            if safe_moves:
                dx, dy = safe_moves[0]
        
        self.last_state = state
        self.last_action = action
        
        return (dx, dy)
    
    def update_with_result(self, snake, food, ate, died, old_snake):
        if not hasattr(self, 'last_state') or not hasattr(self, 'last_action'):
            return
        
        stuck_penalty = self.check_stuck_penalty(snake)
        next_state = self.get_state(snake, food)
        
        reward = self.get_reward(snake, old_snake, food, ate, died, 
                                  self.last_action, stuck_penalty)
        
        self.update_q_table(self.last_state, self.last_action, reward, next_state, died)
        
        self.last_state = None
        self.last_action = None
    
    def get_stats(self):
        strategy_stats = {s: 0 for s in self.strategies}
        total = sum(self.action_stats.values())
        
        if total == 0:
            return {s: 0 for s in self.strategies}
        
        for action, count in self.action_stats.items():
            strategy = action.split('|')[0]
            strategy_stats[strategy] += (count / total) * 100
        
        return strategy_stats
    
    def get_q_table_size(self):
        return len(self.q_table)
    
    def print_action_distribution(self):
        total = sum(self.action_stats.values())
        if total == 0:
            return
        
        print("\n📊 ACTION DISTRIBUTION:")
        for strategy in self.strategies:
            strategy_total = sum(self.action_stats[a] for a in self.all_actions if a.startswith(f"{strategy}|"))
            print(f"  {strategy}: {strategy_total/total*100:.1f}%")
    
    # ========== METHODS FOR SAVING/LOADING WITH SIZE DETECTION ==========
    
    def save_model(self, filename="snake_model.pkl"):
        """Saves the model together with board size"""
        try:
            with open(filename, 'wb') as f:
                pickle.dump({
                    'q_table': self.q_table,
                    'epsilon': self.epsilon,
                    'grid_width': self.grid_width,
                    'grid_height': self.grid_height,
                    'action_stats': self.action_stats
                }, f)
            print(f"💾 Model saved: {filename} ({self.grid_width}x{self.grid_height})")
            return True
        except Exception as e:
            print(f"❌ Error saving: {e}")
            return False
    
    @classmethod
    def load_model(cls, filename="snake_model.pkl", grid_width=None, grid_height=None):
        """
        Loads a model, checking if the size matches
        
        Args:
            filename: File name
            grid_width: Current board width (if None, uses saved one)
            grid_height: Current board height (if None, uses saved one)
        
        Returns:
            HybridSnakeAI instance with loaded or reset model
        """
        if not os.path.exists(filename):
            print(f"📁 {filename} does not exist. Creating new model.")
            if grid_width and grid_height:
                return cls(grid_width, grid_height)
            else:
                return cls(20, 15)
        
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            
            saved_width = data.get('grid_width', 20)
            saved_height = data.get('grid_height', 15)
            
            # Determine target size
            if grid_width is None or grid_height is None:
                target_width = saved_width
                target_height = saved_height
            else:
                target_width = grid_width
                target_height = grid_height
            
            # Create instance with target size
            ai = cls(target_width, target_height)
            
            # Check if sizes match
            if target_width == saved_width and target_height == saved_height:
                # Same size → load Q-Table
                ai.q_table = data.get('q_table', {})
                ai.epsilon = data.get('epsilon', 1.0)
                ai.action_stats = data.get('action_stats', {a: 0 for a in ai.all_actions})
                print(f"✅ Model LOADED: {saved_width}x{saved_height} → {target_width}x{target_height} (same size)")
                print(f"📚 Q-Table size: {len(ai.q_table)} states")
            else:
                # Different size → reset Q-Table but keep hyperparameters
                print(f"⚠️ Model trained on {saved_width}x{saved_height}")
                print(f"📐 Current board: {target_width}x{target_height}")
                print(f"🔄 Resetting Q-Table (states are not compatible)")
                print(f"✅ Keeping hyperparameters: epsilon={ai.epsilon:.4f}")
            
            print(f"🎮 Strategies: {len(ai.strategies)}")
            print(f"🎯 Total maneuvers: {len(ai.all_actions)}")
            
            return ai
            
        except Exception as e:
            print(f"⚠️ Error loading {filename}: {e}")
            print(f"📁 Creating new model for {grid_width}x{grid_height}")
            return cls(grid_width, grid_height)
