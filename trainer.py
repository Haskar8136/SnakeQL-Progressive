import tkinter as tk
from tkinter import ttk, messagebox
import time
import pickle
import os
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Import our modules
import sys
sys.path.append(os.path.dirname(__file__))

from interface import ModernSnakeGUI
from hybrid_snake import HybridSnakeAI

class SnakeTrainer:
    """
    Trainer - WITH MANUAL FILTER
    - Remove episodes BELOW X points
    - Manual control, no automation
    - Instant cleanup with a button
    - Models stored in /pkl folder
    """
    
    def __init__(self, master):
        self.master = master
        master.title("🐍 Snake AI Trainer - Manual Filter")
        master.geometry("1400x900")
        master.configure(bg='#0f0c29')
        
        # Create pkl folder if it doesn't exist
        self.pkl_folder = "pkl"
        if not os.path.exists(self.pkl_folder):
            os.makedirs(self.pkl_folder)
            print(f"📁 Created folder: {self.pkl_folder}/")
        
        # Current board size
        self.current_width = 20
        self.current_height = 15
        
        # Training variables
        self.training = False
        self.training_speed = 30
        self.current_episode = 0
        self.total_episodes = 5000
        self.scores = []
        self.valid_scores = []
        self.discarded_scores = []
        self.avg_scores = []
        self.strategy_stats = []
        self.best_score = 0
        self.valid_episodes_count = 0
        self.discarded_episodes_count = 0
        self.target_episodes = 5000
        
        # MANUAL FILTER: remove episodes below this value
        self.MIN_VALID_SCORE = 10   # Entry threshold for NEW episodes
        self.CLEANUP_THRESHOLD = 10  # Cleanup threshold for PKL
        
        # Disable popups
        self.disable_game_popups()
        
        # Initialize AI and LOAD model
        self.ai = None
        self.load_model_for_current_size()
        
        # Control variables
        self.training_loop_id = None
        self.current_step = 0
        self.max_steps_per_episode = self.current_width * self.current_height * 2
        self.episode_score = 0
        self.episode_start_time = None
        
        # Create UI
        self.create_layout()
        self.create_control_panel()
        self.create_stats_panel()
        self.create_graph()
        self.create_game_frame()
        self.init_game()
        
        print(f"✅ Trainer ready!")
        print(f"📐 Current board: {self.current_width}x{self.current_height}")
        print(f"💾 Current PKL: {self.get_model_filename()}")
        print(f"📊 Episodes in PKL: {len(self.valid_scores)}")
        print(f"🏆 Best score: {self.best_score}")
        print(f"🎯 Entry filter: episodes < {self.MIN_VALID_SCORE} NEVER enter PKL")
        print(f"🧹 Cleanup filter: remove episodes < {self.CLEANUP_THRESHOLD} from PKL")
    
    def get_model_filename(self):
        """Returns the PKL filename based on current board size"""
        return os.path.join(self.pkl_folder, f"snake_{self.current_width}x{self.current_height}.pkl")
    
    def load_model_for_current_size(self):
        """Loads the model for the current board size"""
        filename = self.get_model_filename()
        self.ai = HybridSnakeAI(self.current_width, self.current_height)
        
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                
                if 'q_table' in data:
                    self.ai.q_table = data['q_table']
                if 'epsilon' in data:
                    self.ai.epsilon = data['epsilon']
                
                self.current_episode = data.get('episodes', 0)
                self.valid_scores = data.get('valid_scores', [])
                self.scores = data.get('scores', [])
                self.avg_scores = data.get('avg_scores', [])
                self.best_score = data.get('best_score', 0)
                self.valid_episodes_count = len(self.valid_scores)
                self.discarded_episodes_count = data.get('discarded', 0)
                self.strategy_stats = data.get('strategy_stats', [])
                self.MIN_VALID_SCORE = data.get('min_valid_score', 10)
                self.CLEANUP_THRESHOLD = data.get('cleanup_threshold', 10)
                
                print(f"📂 LOADED: {filename}")
                print(f"   ✅ Episodes in PKL: {len(self.valid_scores)}")
                print(f"   🏆 Best score: {self.best_score}")
                
            except Exception as e:
                print(f"⚠️ Error: {e}")
                self.reset_current_model()
        else:
            print(f"📁 NEW: {filename} (did not exist)")
            self.reset_current_model()
    
    def reset_current_model(self):
        """Resets the current model"""
        self.ai = HybridSnakeAI(self.current_width, self.current_height)
        self.current_episode = 0
        self.valid_scores = []
        self.scores = []
        self.avg_scores = []
        self.best_score = 0
        self.valid_episodes_count = 0
        self.discarded_episodes_count = 0
        self.strategy_stats = []
        self.MIN_VALID_SCORE = 10
        self.CLEANUP_THRESHOLD = 10
    
    def save_current_model(self):
        """Saves the current model to its PKL file"""
        filename = self.get_model_filename()
        
        try:
            data = {
                'q_table': self.ai.q_table,
                'epsilon': self.ai.epsilon,
                'episodes': self.current_episode,
                'valid_scores': self.valid_scores,
                'scores': self.scores,
                'avg_scores': self.avg_scores,
                'best_score': self.best_score,
                'discarded': self.discarded_episodes_count,
                'min_valid_score': self.MIN_VALID_SCORE,
                'cleanup_threshold': self.CLEANUP_THRESHOLD,
                'strategy_stats': self.strategy_stats,
                'grid_width': self.current_width,
                'grid_height': self.current_height
            }
            
            with open(filename, 'wb') as f:
                pickle.dump(data, f)
            
            self.status_label.config(text=f"💾 Saved: {filename}", fg='#00ff9d')
            return True
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {e}", fg='#ff3366')
            return False
    
    def cleanup_pkl(self):
        """
        REMOVES from PKL all episodes with score < CLEANUP_THRESHOLD
        """
        if not self.valid_scores:
            self.status_label.config(text="📁 PKL empty, nothing to clean", fg='#ffd700')
            return 0
        
        old_count = len(self.valid_scores)
        
        # Filter: keep only episodes >= CLEANUP_THRESHOLD
        new_valid_scores = [s for s in self.valid_scores if s >= self.CLEANUP_THRESHOLD]
        removed_count = old_count - len(new_valid_scores)
        
        if removed_count > 0:
            self.valid_scores = new_valid_scores
            self.valid_episodes_count = len(self.valid_scores)
            
            # Recalculate averages
            if self.valid_scores:
                self.avg_scores = []
                for i in range(100, len(self.valid_scores) + 1, 10):
                    avg = sum(self.valid_scores[max(0, i-100):i]) / min(100, i)
                    self.avg_scores.append(avg)
            else:
                self.avg_scores = []
            
            self.save_current_model()
            
            print(f"\n🧹 MANUAL CLEANUP:")
            print(f"   🎯 Threshold: remove episodes < {self.CLEANUP_THRESHOLD}")
            print(f"   🗑️ Removed: {removed_count}")
            print(f"   ✅ Remaining: {len(self.valid_scores)}")
            
            self.status_label.config(text=f"🧹 Removed {removed_count} episodes (< {self.CLEANUP_THRESHOLD})", fg='#ffd700')
        else:
            self.status_label.config(text=f"✅ No episodes < {self.CLEANUP_THRESHOLD}", fg='#00ff9d')
        
        self.update_stats_display()
        self.update_graph()
        
        return removed_count
    
    def change_grid_size(self, width, height):
        """Changes board size and switches to corresponding PKL"""
        if self.training:
            self.stop_training()
        
        self.save_current_model()
        
        self.current_width = width
        self.current_height = height
        self.max_steps_per_episode = width * height * 2
        
        self.load_model_for_current_size()
        
        if hasattr(self, 'game') and self.game:
            if hasattr(self.game, 'change_grid_size'):
                self.game.change_grid_size(width, height)
        
        self.update_stats_display()
        self.update_graph()
    
    def disable_game_popups(self):
        """Disables game confirmation popups"""
        self.original_showinfo = messagebox.showinfo
        self.original_askyesno = messagebox.askyesno
        messagebox.showinfo = lambda *args, **kwargs: None
        messagebox.askyesno = lambda *args, **kwargs: True
    
    def restore_game_popups(self):
        """Restores game popups"""
        messagebox.showinfo = self.original_showinfo
        messagebox.askyesno = self.original_askyesno
    
    def create_layout(self):
        """Creates scrollable layout"""
        self.main_canvas = tk.Canvas(self.master, bg='#0f0c29', highlightthickness=0)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = tk.Scrollbar(self.master, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.inner_frame = tk.Frame(self.main_canvas, bg='#0f0c29')
        self.main_canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW, width=1380)
        self.inner_frame.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.bind("<MouseWheel>", lambda e: self.main_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    def create_control_panel(self):
        """Control panel"""
        control_frame = tk.Frame(self.inner_frame, bg='#1a1638', relief=tk.RIDGE, bd=2)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(control_frame, text="🎮 CONTROL - MANUAL FILTER",
                font=('Arial', 16, 'bold'), fg='#00ff9d', bg='#1a1638').pack(pady=10)
        
        # Board size selector
        size_frame = tk.Frame(control_frame, bg='#1a1638')
        size_frame.pack(pady=10)
        
        tk.Label(size_frame, text="📐 Select Board Size:", fg='#8888ff', bg='#1a1638',
                font=('Arial', 12)).pack(side=tk.LEFT, padx=10)
        
        sizes = [("5x5", 5, 5), ("10x10", 10, 10), ("20x15", 20, 15)]
        for text, w, h in sizes:
            btn = tk.Button(size_frame, text=text,
                          command=lambda width=w, height=h: self.change_grid_size(width, height),
                          bg='#0f0c29', fg='#00ff9d', 
                          font=('Arial', 11, 'bold'),
                          padx=15, pady=5)
            btn.pack(side=tk.LEFT, padx=5)
        
        self.pkl_label = tk.Label(control_frame, text=f"📁 PKL: {self.get_model_filename()}",
                                  fg='#ffd700', bg='#1a1638', font=('Arial', 10))
        self.pkl_label.pack(pady=5)
        
        btn_frame = tk.Frame(control_frame, bg='#1a1638')
        btn_frame.pack(pady=10)
        
        self.start_btn = tk.Button(btn_frame, text="▶ START",
                                  command=self.start_training,
                                  bg='#00ff9d', fg='#0f0c29',
                                  font=('Arial', 12, 'bold'),
                                  padx=20, pady=10, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="⏸ PAUSE",
                                 command=self.stop_training,
                                 bg='#ff3366', fg='white',
                                 font=('Arial', 12, 'bold'),
                                 padx=20, pady=10, width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Episodes to train
        episodes_frame = tk.Frame(control_frame, bg='#1a1638')
        episodes_frame.pack(pady=5)
        
        tk.Label(episodes_frame, text="🎯 Episodes to train:", fg='#8888ff', bg='#1a1638').pack(side=tk.LEFT)
        self.episodes_entry = tk.Entry(episodes_frame, width=8,
                                       bg='#0f0c29', fg='#00ff9d',
                                       insertbackground='white', font=('Arial', 12))
        self.episodes_entry.insert(0, "5000")
        self.episodes_entry.pack(side=tk.LEFT, padx=10)
        
        # Speed
        tk.Label(episodes_frame, text="⚡ Speed:", fg='#8888ff', bg='#1a1638').pack(side=tk.LEFT, padx=(20,0))
        self.speed_scale = tk.Scale(episodes_frame, from_=10, to=200,
                                   orient=tk.HORIZONTAL,
                                   command=self.change_speed,
                                   bg='#1a1638', fg='#00ff9d',
                                   length=120)
        self.speed_scale.set(self.training_speed)
        self.speed_scale.pack(side=tk.LEFT, padx=10)
        
        # ENTRY FILTER (for NEW episodes)
        filter_frame = tk.Frame(control_frame, bg='#1a1638')
        filter_frame.pack(pady=5)
        
        tk.Label(filter_frame, text="🎯 ENTRY FILTER (episodes < X NEVER enter PKL):", 
                 fg='#8888ff', bg='#1a1638').pack(side=tk.LEFT)
        
        self.filter_var = tk.IntVar(value=self.MIN_VALID_SCORE)
        self.filter_scale = tk.Scale(filter_frame, from_=0, to=500,
                                     orient=tk.HORIZONTAL,
                                     variable=self.filter_var,
                                     command=self.change_filter_threshold,
                                     bg='#1a1638', fg='#00ff9d',
                                     length=200)
        self.filter_scale.pack(side=tk.LEFT, padx=10)
        
        self.filter_label = tk.Label(filter_frame, text=f"{self.MIN_VALID_SCORE}",
                                     fg='#ffd700', bg='#1a1638', font=('Arial', 12, 'bold'))
        self.filter_label.pack(side=tk.LEFT, padx=5)
        
        # CLEANUP FILTER (to remove from PKL)
        cleanup_frame = tk.Frame(control_frame, bg='#1a1638')
        cleanup_frame.pack(pady=5)
        
        tk.Label(cleanup_frame, text="🧹 CLEANUP FILTER (remove from PKL episodes < X):", 
                 fg='#8888ff', bg='#1a1638').pack(side=tk.LEFT)
        
        self.cleanup_var = tk.IntVar(value=self.CLEANUP_THRESHOLD)
        self.cleanup_scale = tk.Scale(cleanup_frame, from_=0, to=500,
                                      orient=tk.HORIZONTAL,
                                      variable=self.cleanup_var,
                                      command=self.change_cleanup_threshold,
                                      bg='#1a1638', fg='#ff3366',
                                      length=200)
        self.cleanup_scale.pack(side=tk.LEFT, padx=10)
        
        self.cleanup_label = tk.Label(cleanup_frame, text=f"{self.CLEANUP_THRESHOLD}",
                                      fg='#ff3366', bg='#1a1638', font=('Arial', 12, 'bold'))
        self.cleanup_label.pack(side=tk.LEFT, padx=5)
        
        # Manual cleanup button
        tk.Button(cleanup_frame, text="🧹 REMOVE LOW EPISODES NOW",
                 command=self.cleanup_pkl,
                 bg='#ff3366', fg='white',
                 font=('Arial', 10, 'bold'),
                 padx=15, pady=3).pack(side=tk.LEFT, padx=20)
        
        # Save/Reset buttons
        button_frame = tk.Frame(control_frame, bg='#1a1638')
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="💾 SAVE MODEL",
                 command=self.save_current_model,
                 bg='#4caf50', fg='white',
                 font=('Arial', 11, 'bold'),
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🔄 RESET MODEL",
                 command=self.reset_current_model,
                 bg='#ff9800', fg='white',
                 font=('Arial', 11, 'bold'),
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)
    
    def create_stats_panel(self):
        """Statistics panel"""
        stats_frame = tk.LabelFrame(self.inner_frame, text="📊 STATISTICS",
                                    font=('Arial', 12, 'bold'), fg='#ffd700',
                                    bg='#1a1638', relief=tk.RIDGE)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        grid_frame = tk.Frame(stats_frame, bg='#1a1638')
        grid_frame.pack(padx=10, pady=10)
        
        stats = [
            ("🎯 Total episodes:", "episode", "0"),
            ("✅ In PKL:", "valid", "0"),
            ("🗑️ Discarded (never entered):", "discarded", "0"),
            ("🏆 Best score:", "best", "0"),
            ("📈 Current average:", "avg", "0"),
            ("🔍 Epsilon:", "epsilon", "1.0"),
            ("📚 Q-Table:", "qsize", "0"),
            ("📐 Board size:", "gridsize", "20x15"),
            ("🎯 Entry filter:", "filter", "10"),
            ("🧹 Cleanup filter:", "cleanup", "10")
        ]
        
        self.stats_vars = {}
        
        for i, (label, key, default) in enumerate(stats):
            row = i // 2
            col = i % 2
            
            frame = tk.Frame(grid_frame, bg='#1a1638')
            frame.grid(row=row, column=col, padx=20, pady=5, sticky="w")
            
            tk.Label(frame, text=label, font=('Arial', 11),
                    fg='#8888ff', bg='#1a1638').pack(side=tk.LEFT)
            
            var = tk.StringVar(value=str(default))
            self.stats_vars[key] = var
            
            tk.Label(frame, textvariable=var, font=('Arial', 14, 'bold'),
                    fg='#00ff9d', bg='#1a1638').pack(side=tk.LEFT, padx=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(stats_frame, variable=self.progress_var,
                                           maximum=100, length=400, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        self.status_label = tk.Label(stats_frame, text="🟡 Waiting...",
                                     font=('Arial', 11), fg='#ffd700', bg='#1a1638')
        self.status_label.pack(pady=5)
    
    def create_graph(self):
        """Progress graph"""
        graph_frame = tk.LabelFrame(self.inner_frame, text="📈 PROGRESS",
                                    font=('Arial', 12, 'bold'), fg='#ffd700',
                                    bg='#1a1638', relief=tk.RIDGE)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 6))
        self.fig.patch.set_facecolor('#1a1638')
        self.fig.subplots_adjust(hspace=0.3)
        
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor('#0f0c29')
            ax.tick_params(colors='white')
        
        self.ax1.set_xlabel('Valid Episode', color='white')
        self.ax1.set_ylabel('Score', color='white')
        self.ax1.set_title('Learning Progress (only episodes in PKL)', color='white')
        
        self.ax2.set_xlabel('Episode', color='white')
        self.ax2.set_ylabel('Usage (%)', color='white')
        self.ax2.set_title('Strategies Distribution', color='white')
        self.ax2.set_ylim(0, 100)
        
        self.canvas_graph = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_game_frame(self):
        """Game view frame"""
        game_frame = tk.LabelFrame(self.inner_frame, text="🎮 GAME VIEW",
                                   font=('Arial', 12, 'bold'), fg='#ffd700',
                                   bg='#1a1638', relief=tk.RIDGE)
        game_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.game_container = tk.Frame(game_frame, bg='#0f0c29')
        self.game_container.pack(expand=True, padx=10, pady=10)
    
    def init_game(self):
        """Initializes the game"""
        self.game_window = tk.Toplevel(self.master)
        self.game_window.title(f"Snake AI - {self.current_width}x{self.current_height}")
        self.game_window.configure(bg='#0f0c29')
        
        x = self.master.winfo_x() + self.master.winfo_width() + 10
        y = self.master.winfo_y()
        self.game_window.geometry(f"+{x}+{y}")
        
        self.game = ModernSnakeGUI(self.game_window)
        
        if hasattr(self.game, 'change_grid_size'):
            self.game.change_grid_size(self.current_width, self.current_height)
        
        self.game_window.protocol("WM_DELETE_WINDOW", self.on_game_close)
    
    def change_filter_threshold(self, val):
        """Changes ENTRY filter (for new episodes)"""
        self.MIN_VALID_SCORE = int(val)
        self.filter_label.config(text=str(self.MIN_VALID_SCORE))
        self.stats_vars['filter'].set(str(self.MIN_VALID_SCORE))
        self.status_label.config(text=f"🎯 Entry filter: episodes < {self.MIN_VALID_SCORE} NEVER enter PKL", fg='#ffd700')
    
    def change_cleanup_threshold(self, val):
        """Changes CLEANUP filter (to remove from PKL)"""
        self.CLEANUP_THRESHOLD = int(val)
        self.cleanup_label.config(text=str(self.CLEANUP_THRESHOLD))
        self.stats_vars['cleanup'].set(str(self.CLEANUP_THRESHOLD))
        self.status_label.config(text=f"🧹 Cleanup filter: remove from PKL episodes < {self.CLEANUP_THRESHOLD}", fg='#ffd700')
    
    def is_valid_episode(self, score):
        return score >= self.MIN_VALID_SCORE
    
    def start_training(self):
        if self.training:
            return
        
        self.training = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        try:
            self.total_episodes = int(self.episodes_entry.get())
        except:
            self.total_episodes = 5000
        
        self.target_episodes = self.current_episode + self.total_episodes
        self.run_episode()
    
    def stop_training(self):
        self.training = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.training_loop_id:
            self.master.after_cancel(self.training_loop_id)
            self.training_loop_id = None
        
        self.save_current_model()
    
    def run_episode(self):
        if not self.training:
            return
        
        if self.game:
            self.game.reset_game_clean()
        
        self.current_step = 0
        self.episode_score = 0
        self.master.after(100, self.episode_step)
    
    def episode_step(self):
        if not self.training:
            return
        
        if not self.game or not self.game.game_running:
            self.end_episode()
            return
        
        if self.current_step >= self.max_steps_per_episode:
            if self.game:
                self.game.game_running = False
            self.end_episode()
            return
        
        old_snake = self.game.snake_positions.copy()
        old_score = self.game.current_score
        
        dx, dy = self.ai.get_action(self.game.snake_positions, self.game.food_position)
        self.game.move_snake(dx, dy)
        
        ate = self.game.current_score > old_score
        died = not self.game.game_running
        
        self.ai.update_with_result(
            self.game.snake_positions,
            self.game.food_position,
            ate,
            died,
            old_snake
        )
        
        self.episode_score = self.game.current_score
        self.update_stats_display()
        
        self.current_step += 1
        self.training_loop_id = self.master.after(self.training_speed, self.episode_step)
    
    def end_episode(self):
        if not self.training:
            return
        
        score = self.episode_score
        episode_num = self.current_episode + 1
        self.scores.append(score)
        
        # ENTRY FILTER: only enter PKL if above threshold
        if self.is_valid_episode(score):
            self.valid_scores.append(score)
            self.valid_episodes_count += 1
            
            if score > self.best_score:
                self.best_score = score
                self.status_label.config(text=f"🏆 RECORD! {score} points", fg='#ffd700')
            
            if self.valid_scores:
                avg = sum(self.valid_scores[-100:]) / min(len(self.valid_scores), 100)
                self.avg_scores.append(avg)
            
            stats = self.ai.get_stats()
            self.strategy_stats.append(stats)
            
            print(f"✅ Ep{episode_num}: {score} points (ENTERED PKL)")
        else:
            self.discarded_scores.append(score)
            self.discarded_episodes_count += 1
            print(f"🗑️ Ep{episode_num}: {score} points (DID NOT enter - < {self.MIN_VALID_SCORE})")
        
        self.current_episode += 1
        self.ai.decay_epsilon()
        
        self.update_stats_display()
        self.update_graph()
        
        if self.current_episode % 50 == 0:
            quality = (self.valid_episodes_count / max(self.current_episode, 1)) * 100
            print(f"📊 Ep{self.current_episode}: PKL={len(self.valid_scores)} episodes | Q-Table={len(self.ai.q_table)} | Quality={quality:.0f}%")
        
        if self.current_episode >= self.target_episodes:
            self.training = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.save_current_model()
            print(f"\n🎉 TRAINING COMPLETED! {len(self.valid_scores)} episodes in PKL")
        else:
            self.master.after(10, self.run_episode)
    
    def update_stats_display(self):
        self.stats_vars['episode'].set(str(self.current_episode))
        self.stats_vars['valid'].set(str(len(self.valid_scores)))
        self.stats_vars['discarded'].set(str(self.discarded_episodes_count))
        self.stats_vars['best'].set(str(self.best_score))
        
        if self.valid_scores:
            avg = sum(self.valid_scores[-100:]) / min(len(self.valid_scores), 100)
            self.stats_vars['avg'].set(f"{avg:.1f}")
        else:
            self.stats_vars['avg'].set("0")
        
        self.stats_vars['epsilon'].set(f"{self.ai.epsilon:.4f}")
        self.stats_vars['qsize'].set(str(len(self.ai.q_table)))
        self.stats_vars['gridsize'].set(f"{self.current_width}x{self.current_height}")
        self.stats_vars['filter'].set(str(self.MIN_VALID_SCORE))
        self.stats_vars['cleanup'].set(str(self.CLEANUP_THRESHOLD))
        
        self.pkl_label.config(text=f"📁 PKL: {self.get_model_filename()} | {len(self.valid_scores)} episodes")
        
        episodes_in_session = self.current_episode - (self.target_episodes - self.total_episodes)
        if self.total_episodes > 0:
            progress = (episodes_in_session / self.total_episodes) * 100
            self.progress_var.set(max(0, min(100, progress)))
        
        if self.training:
            quality = (len(self.valid_scores) / max(self.current_episode, 1)) * 100
            self.status_label.config(text=f"🟢 Ep{self.current_episode} | PKL:{len(self.valid_scores)} | ✅{quality:.0f}%")
    
    def update_graph(self):
        def _update():
            self.ax1.clear()
            self.ax2.clear()
            
            if self.valid_scores:
                display_scores = self.valid_scores[-500:] if len(self.valid_scores) > 500 else self.valid_scores
                display_avg = self.avg_scores[-500:] if len(self.avg_scores) > 500 else self.avg_scores
                
                self.ax1.plot(display_scores, alpha=0.3, color='#00ff9d', linewidth=0.5, marker='.', markersize=2)
                if display_avg:
                    self.ax1.plot(display_avg, color='#ff3366', linewidth=2, label='Average')
                self.ax1.axhline(y=self.best_score, color='#ffd700', linestyle='--', label=f'Record: {self.best_score}')
                self.ax1.axhline(y=self.MIN_VALID_SCORE, color='#8888ff', linestyle=':', linewidth=1, label=f'Entry filter: {self.MIN_VALID_SCORE}')
                self.ax1.legend(loc='upper left', facecolor='#1a1638', labelcolor='white')
                self.ax1.tick_params(colors='white')
                self.ax1.set_ylim(bottom=0)
            
            if self.strategy_stats:
                strategies = ['AGGRESSIVE', 'BALANCED', 'SAFE', 'EXPLORE']
                display_stats = self.strategy_stats[-200:] if len(self.strategy_stats) > 200 else self.strategy_stats
                colors = {'AGGRESSIVE': '#ff3366', 'BALANCED': '#00ff9d', 'SAFE': '#ffd700', 'EXPLORE': '#8888ff'}
                
                for strategy in strategies:
                    usage = [stats.get(strategy, 0) for stats in display_stats]
                    if usage:
                        self.ax2.plot(usage, color=colors.get(strategy, '#8888ff'), linewidth=1.5, label=strategy, alpha=0.8)
                
                self.ax2.legend(loc='upper left', facecolor='#1a1638', labelcolor='white')
                self.ax2.tick_params(colors='white')
                self.ax2.set_ylim(0, 100)
            
            self.canvas_graph.draw()
        
        self.master.after(0, _update)
    
    def change_speed(self, val):
        self.training_speed = int(val)
    
    def on_game_close(self):
        if self.training:
            self.stop_training()
        if self.game_window:
            self.game_window.destroy()
    
    def on_closing(self):
        if self.training:
            self.stop_training()
        self.save_current_model()
        self.restore_game_popups()
        if self.game_window:
            self.game_window.destroy()
        self.master.destroy()

def main():
    root = tk.Tk()
    app = SnakeTrainer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
