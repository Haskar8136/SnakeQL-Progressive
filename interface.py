import tkinter as tk
from tkinter import messagebox, ttk
import random
import math

class ModernSnakeGUI:
    def __init__(self, master):
        self.master = master
        master.title("🐍 SNAKE DELUXE - Animated Interface")
        master.resizable(False, False)
        
        # Base configuration
        self.cell_size = 30
        self.current_grid_size = 20
        self.grid_width = 20
        self.grid_height = 15
        
        # Modern colors
        self.colors = {
            'bg_start': '#0f0c29',
            'bg_end': '#302b63',
            'grid': '#2a2448',
            'snake_head': '#00ff9d',
            'snake_body': '#00d4ff',
            'snake_body_dark': '#0099cc',
            'food': '#ff3333',
            'food_glow': '#ff6666',
            'food_leaf': '#00cc44',
            'shadow': '#1a1a1a'
        }
        
        # Animation variables
        self.animation_frame = 0
        self.food_pulse = 0
        self.food_direction = 1
        self.current_score = 0
        self.game_running = True
        self.is_resetting = False  # Prevent multiple resets
        
        # Main frame
        self.main_frame = tk.Frame(master, bg='#0f0c29')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top control panel
        self.create_control_panel()
        
        # Score panel
        self.create_score_panel()
        
        # Canvas frame
        self.canvas_frame = tk.Frame(self.main_frame, bg='#0f0c29', highlightthickness=0)
        self.canvas_frame.pack(pady=10)
        
        # Main canvas
        self.canvas = None
        self.create_canvas()
        
        # Initialize game
        self.init_game()
        
        # Start animations
        self.animate()
        
        # Keyboard events
        master.bind("<KeyPress>", self.on_key_press)
        
        # Instructions
        self.create_instructions()
    
    def create_control_panel(self):
        """Control panel for changing board size"""
        control_frame = tk.Frame(self.main_frame, bg='#0f0c29')
        control_frame.pack(pady=(0, 10))
        
        tk.Label(
            control_frame,
            text="Board Size:",
            font=('Arial', 12),
            fg='#8888ff',
            bg='#0f0c29'
        ).pack(side=tk.LEFT, padx=10)
        
        sizes = [
            ("5x5", 5, 5),
            ("10x10", 10, 10),
            ("20x15", 20, 15)
        ]
        
        for text, width, height in sizes:
            btn = tk.Button(
                control_frame,
                text=text,
                font=('Arial', 10, 'bold'),
                bg='#1a1638',
                fg='#00ff9d',
                activebackground='#00ff9d',
                activeforeground='#0f0c29',
                relief=tk.FLAT,
                padx=15,
                pady=5,
                command=lambda w=width, h=height: self.change_grid_size(w, h)
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        tk.Button(
            control_frame,
            text="🔄 Reset Game",
            font=('Arial', 10, 'bold'),
            bg='#ff3366',
            fg='white',
            activebackground='#cc0033',
            activeforeground='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.reset_game_clean
        ).pack(side=tk.LEFT, padx=20)
    
    def create_canvas(self):
        """Creates or recreates the canvas with current size"""
        if self.canvas:
            self.canvas.destroy()
        
        width = self.grid_width * self.cell_size
        height = self.grid_height * self.cell_size
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=width,
            height=height,
            bg='#1a1638',
            highlightthickness=2,
            highlightcolor='#00ff9d',
            highlightbackground='#00ff9d'
        )
        self.canvas.pack()
        
        # Apply visual effects
        self.apply_gradient()
        self.draw_decorative_grid()
    
    def clear_canvas_objects(self):
        """Clears all canvas objects (snake, food, etc.)"""
        if hasattr(self, 'snake_rects'):
            for rect in self.snake_rects:
                self.canvas.delete(rect)
        if hasattr(self, 'snake_eyes'):
            for eye in self.snake_eyes:
                self.canvas.delete(eye)
        if hasattr(self, 'food_rect'):
            self.canvas.delete(self.food_rect)
        if hasattr(self, 'food_leaf'):
            self.canvas.delete(self.food_leaf)
        if hasattr(self, 'food_shine'):
            self.canvas.delete(self.food_shine)
        if hasattr(self, 'food_shadow'):
            self.canvas.delete(self.food_shadow)
        
        # Clear lists
        self.snake_rects = []
        self.snake_eyes = []
    
    def reset_game(self):
        """Public method to reset the game (used by trainer)"""
        self.reset_game_clean()
    
    def change_grid_size(self, width, height):
        """Changes board size and completely resets the game"""
        if self.is_resetting:
            return
            
        self.is_resetting = True
        self.game_running = False
        
        # Clear canvas completely
        self.clear_canvas_objects()
        
        # Update dimensions
        self.grid_width = width
        self.grid_height = height
        
        # Recreate canvas with new size
        self.create_canvas()
        
        # Clean game reset
        self.init_game()
        
        # Adjust window size
        self.adjust_window_size()
        
        self.is_resetting = False
    
    def reset_game_clean(self):
        """Complete game reset without changing size"""
        if self.is_resetting:
            return
            
        self.is_resetting = True
        self.game_running = False
        
        # Clear canvas
        self.clear_canvas_objects()
        
        # Reset game
        self.init_game()
        
        self.is_resetting = False
    
    def adjust_window_size(self):
        """Adjusts window size based on grid dimensions"""
        window_width = self.grid_width * self.cell_size + 80
        window_height = self.grid_height * self.cell_size + 250
        
        # Center window
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.master.geometry(f'{window_width}x{window_height}+{x}+{y}')
    
    def create_score_panel(self):
        """Creates a modern score panel"""
        self.score_frame = tk.Frame(self.main_frame, bg='#1a1638', relief=tk.FLAT)
        self.score_frame.pack(pady=(0, 15), ipadx=20, ipady=10)
        
        border_frame = tk.Frame(self.score_frame, bg='#00ff9d', height=2)
        border_frame.pack(fill=tk.X, padx=5)
        
        self.score_label = tk.Label(
            self.score_frame,
            text="🍎 SCORE: 0",
            font=('Courier', 20, 'bold'),
            fg='#00ff9d',
            bg='#1a1638'
        )
        self.score_label.pack(side=tk.LEFT, padx=20)
        
        self.grid_info_label = tk.Label(
            self.score_frame,
            text=f"📐 {self.grid_width}x{self.grid_height}",
            font=('Courier', 14),
            fg='#ffd700',
            bg='#1a1638'
        )
        self.grid_info_label.pack(side=tk.LEFT, padx=20)
    
    def apply_gradient(self):
        """Applies a gradient to the canvas background"""
        width = self.grid_width * self.cell_size
        height = self.grid_height * self.cell_size
        
        for y in range(0, height, 2):
            ratio = y / height
            r = int(15 + 10 * ratio)
            g = int(12 + 30 * ratio)
            b = int(40 + 40 * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, y, width, y, fill=color, width=1)
    
    def draw_decorative_grid(self):
        """Draws a decorative grid with bright dots"""
        for x in range(0, self.grid_width * self.cell_size, self.cell_size):
            for y in range(0, self.grid_height * self.cell_size, self.cell_size):
                brightness = 30 + (x + y) % 50
                color = f'#{brightness:02x}{brightness:02x}{brightness+20:02x}'
                self.canvas.create_oval(
                    x-1, y-1, x+1, y+1,
                    fill=color,
                    outline=''
                )
    
    def init_game(self):
        """Initializes or completely resets the game"""
        # Clear visually
        self.clear_canvas_objects()
        
        # Initial snake position (center)
        center_x = max(1, self.grid_width // 2)
        center_y = max(1, self.grid_height // 2)
        
        # Ensure snake fits on board
        if self.grid_width >= 3 and self.grid_height >= 3:
            self.snake_positions = [
                (center_x, center_y),
                (center_x - 1, center_y),
                (center_x - 2, center_y)
            ]
        else:
            # For very small boards (5x5)
            self.snake_positions = [
                (1, 1),
                (0, 1),
                (0, 0)
            ]
        
        # Game variables
        self.food_position = None
        self.current_score = 0
        self.game_running = True
        self.leaf_angle = 0
        self.food_pulse = 0
        
        # Update UI
        self.update_score_display()
        
        # Generate food and draw
        self.spawn_food()
        self.draw_snake()
        self.draw_food()
    
    def draw_snake(self):
        """Draws the snake with gradient effect and eyes"""
        # Clear previous snake
        for rect in self.snake_rects:
            self.canvas.delete(rect)
        for eye in self.snake_eyes:
            self.canvas.delete(eye)
        
        self.snake_rects = []
        self.snake_eyes = []
        
        for i, (x, y) in enumerate(self.snake_positions):
            x1 = x * self.cell_size
            y1 = y * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            
            if i == 0:
                color = self.colors['snake_head']
            else:
                color = self.colors['snake_body']
            
            rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline=self.colors['snake_body_dark'],
                width=2
            )
            self.snake_rects.append(rect)
            
            # Eyes only on head and if there's enough space
            if i == 0 and self.cell_size >= 20 and self.game_running:
                eye_size = max(2, self.cell_size // 8)
                eye_offset = self.cell_size // 4
                
                left_eye = self.canvas.create_oval(
                    x1 + eye_offset, y1 + eye_offset,
                    x1 + eye_offset + eye_size, y1 + eye_offset + eye_size,
                    fill='white', outline='black', width=1
                )
                right_eye = self.canvas.create_oval(
                    x2 - eye_offset - eye_size, y1 + eye_offset,
                    x2 - eye_offset, y1 + eye_offset + eye_size,
                    fill='white', outline='black', width=1
                )
                left_pupil = self.canvas.create_oval(
                    x1 + eye_offset + 1, y1 + eye_offset + 1,
                    x1 + eye_offset + eye_size - 1, y1 + eye_offset + eye_size - 1,
                    fill='black', outline=''
                )
                right_pupil = self.canvas.create_oval(
                    x2 - eye_offset - eye_size + 1, y1 + eye_offset + 1,
                    x2 - eye_offset - 1, y1 + eye_offset + eye_size - 1,
                    fill='black', outline=''
                )
                self.snake_eyes.extend([left_eye, right_eye, left_pupil, right_pupil])
    
    def spawn_food(self):
        """Generates an apple in a valid position"""
        if not self.game_running:
            return
            
        max_attempts = 100
        for _ in range(max_attempts):
            new_food = (
                random.randint(0, self.grid_width - 1),
                random.randint(0, self.grid_height - 1)
            )
            if new_food not in self.snake_positions:
                self.food_position = new_food
                return
        
        # No space left, you win!
        self.game_running = False
        messagebox.showinfo("VICTORY!", f"🏆 You filled the board!\n🍎 Final score: {self.current_score}")
        self.reset_game_clean()
    
    def draw_food(self):
        """Draws an apple with a subtle pulsation effect"""
        if hasattr(self, 'food_rect'):
            self.canvas.delete(self.food_rect)
        if hasattr(self, 'food_leaf'):
            self.canvas.delete(self.food_leaf)
        if hasattr(self, 'food_shine'):
            self.canvas.delete(self.food_shine)
        if hasattr(self, 'food_shadow'):
            self.canvas.delete(self.food_shadow)
        
        if self.food_position and self.game_running:
            x, y = self.food_position
            x1 = x * self.cell_size
            y1 = y * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            
            pulse = abs(math.sin(self.food_pulse * 0.1)) * 2
            padding = 3 + int(pulse)
            
            # Shadow
            self.food_shadow = self.canvas.create_oval(
                x1+2, y1+2, x2+2, y2+2,
                fill='#222222',
                outline=''
            )
            
            # Apple body
            self.food_rect = self.canvas.create_oval(
                x1+padding, y1+padding, x2-padding, y2-padding,
                fill=self.colors['food'],
                outline='#cc0000',
                width=2
            )
            
            # Leaf (only if cell is large enough)
            if self.cell_size >= 20:
                self.leaf_angle += 0.05
                leaf_offset = int(math.sin(self.leaf_angle) * 2)
                
                self.food_leaf = self.canvas.create_polygon(
                    x2-8, y1+5 + leaf_offset,
                    x2-2, y1+2,
                    x2-2, y1+8,
                    fill=self.colors['food_leaf'],
                    outline='#009933',
                    width=1
                )
                
                # Shine
                self.food_shine = self.canvas.create_oval(
                    x1+self.cell_size//2.5, y1+self.cell_size//3,
                    x1+self.cell_size//1.8, y1+self.cell_size//2.5,
                    fill='white',
                    outline='',
                    stipple='gray50'
                )
    
    def animate(self):
        """Continuous interface animation"""
        if self.game_running:
            self.food_pulse += self.food_direction
            if self.food_pulse > 30 or self.food_pulse < 0:
                self.food_direction *= -1
            self.draw_food()
        
        self.master.after(50, self.animate)
    
    def move_snake(self, dx, dy):
        """Snake movement"""
        if not self.game_running:
            return
            
        head_x, head_y = self.snake_positions[0]
        new_head = (head_x + dx, head_y + dy)
        
        # Check boundaries
        if (0 <= new_head[0] < self.grid_width and
            0 <= new_head[1] < self.grid_height):
            
            # Check self-collision
            if new_head in self.snake_positions:
                self.game_over()
                return
            
            self.snake_positions.insert(0, new_head)
            
            if new_head == self.food_position:
                self.current_score += 10
                self.update_score_display()
                self.spawn_food()
                self.animate_score()
            else:
                self.snake_positions.pop()
            
            self.draw_snake()
            self.draw_food()
        else:
            self.game_over()
    
    def game_over(self):
        """Ends the game and makes the snake disappear"""
        self.game_running = False
        
        # Make snake disappear visually
        for rect in self.snake_rects:
            self.canvas.delete(rect)
        for eye in self.snake_eyes:
            self.canvas.delete(eye)
        self.snake_rects = []
        self.snake_eyes = []
        
        # Show message
        messagebox.showinfo("Game Over", f"💀 The snake died!\n🍎 Score: {self.current_score}")
        
        # Clean game reset
        self.reset_game_clean()
    
    def animate_score(self):
        """Animates the score text"""
        def update_font(size):
            self.score_label.config(font=('Courier', size, 'bold'))
        
        original_size = 20
        for size in range(original_size, original_size + 10, 2):
            self.master.after((size - original_size) * 20, lambda s=size: update_font(s))
        for size in range(original_size + 10, original_size, -2):
            self.master.after((size - original_size) * 20 + 200, lambda s=size: update_font(s))
    
    def update_score_display(self):
        """Updates the score in the interface"""
        self.score_label.config(text=f"🍎 SCORE: {self.current_score}")
        self.grid_info_label.config(text=f"📐 {self.grid_width}x{self.grid_height}")
    
    def create_instructions(self):
        """Creates stylish instructions"""
        inst_frame = tk.Frame(self.main_frame, bg='#0f0c29')
        inst_frame.pack(pady=10)
        
        instructions = [
            "🎮 CONTROLS:",
            "← ↑ → ↓  to move the snake",
            "🍎 Eat the red apples",
            "📏 Change board size above",
            "💀 When it dies, the snake disappears"
        ]
        
        for text in instructions:
            label = tk.Label(
                inst_frame,
                text=text,
                font=('Arial', 10),
                fg='#8888ff',
                bg='#0f0c29'
            )
            label.pack()
    
    def on_key_press(self, event):
        """Handles keyboard events"""
        if not self.game_running:
            return
            
        key = event.keysym
        if key == "Left":
            self.move_snake(-1, 0)
        elif key == "Right":
            self.move_snake(1, 0)
        elif key == "Up":
            self.move_snake(0, -1)
        elif key == "Down":
            self.move_snake(0, 1)

def main():
    root = tk.Tk()
    root.configure(bg='#0f0c29')
    root.geometry('680x700+100+100')
    
    app = ModernSnakeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
