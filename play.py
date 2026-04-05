#!/usr/bin/env python3
"""
SnakeQL-Progressive - Model Tester / Demo Mode
Loads a trained model and lets the AI play automatically
Automatically switches model when board size changes
"""

import tkinter as tk
from tkinter import ttk, messagebox
import argparse
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from hybrid_snake import HybridSnakeAI
from interface import ModernSnakeGUI


class SnakeDemo:
    """
    Demo mode - Loads trained model and plays automatically
    Automatically switches model when board size changes
    No training, just pure exploitation (epsilon = 0)
    """
    
    def __init__(self, initial_width=10, initial_height=10, speed=50):
        """
        Initialize the demo mode
        
        Args:
            initial_width: Initial board width (5, 10, or 20)
            initial_height: Initial board height (5, 10, or 15)
            speed: Movement speed in milliseconds (default: 50)
        """
        self.current_width = initial_width
        self.current_height = initial_height
        self.speed = speed
        self.running = True
        self.ai = None
        
        print(f"\n{'='*50}")
        print(f"🐍 SnakeQL-Progressive - Demo Mode")
        print(f"{'='*50}")
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(f"🐍 Snake AI - Demo Mode ({self.current_width}x{self.current_height})")
        
        # Create and configure game
        self.game = ModernSnakeGUI(self.root)
        
        # Override the change_grid_size method to switch models
        self.original_change_grid_size = self.game.change_grid_size
        self.game.change_grid_size = self.on_board_size_change
        
        # Force initial board size
        self.game.change_grid_size(self.current_width, self.current_height)
        
        # Load initial model
        self.load_model_for_current_size()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the game loop
        self.play()
        
        print(f"\n🎮 Starting demo...")
        print(f"⚡ Speed: {speed}ms per move")
        print(f"🔄 Models change automatically with board size")
        print(f"❌ Close the window to exit")
        print(f"{'='*50}\n")
        
        # Start main loop
        self.root.mainloop()
    
    def get_model_filename(self, width, height):
        """Get model filename for given board size"""
        return os.path.join("pkl", f"snake_{width}x{height}.pkl")
    
    def load_model_for_current_size(self):
        """Load the model for the current board size"""
        filename = self.get_model_filename(self.current_width, self.current_height)
        
        print(f"\n📐 Board size: {self.current_width}x{self.current_height}")
        print(f"💾 Loading model: {filename}")
        
        if os.path.exists(filename):
            self.ai = HybridSnakeAI.load_model(filename, self.current_width, self.current_height)
            print(f"✅ Model loaded successfully!")
        else:
            print(f"⚠️ Model not found: {filename}")
            print(f"📁 Creating new untrained model...")
            self.ai = HybridSnakeAI(self.current_width, self.current_height)
        
        # Set to EXPLOITATION MODE (no exploration)
        self.ai.epsilon = 0.0
        print(f"🔧 Mode: EXPLOITATION ONLY (epsilon = 0)")
        print(f"📚 Q-Table size: {self.ai.get_q_table_size()} states")
        
        # Show strategy distribution if available
        stats = self.ai.get_stats()
        if sum(stats.values()) > 0:
            print(f"\n📊 Learned strategy distribution:")
            for strategy, percent in stats.items():
                print(f"   {strategy}: {percent:.1f}%")
        
        # Update window title
        self.root.title(f"🐍 Snake AI - Demo Mode ({self.current_width}x{self.current_height}) | Model loaded")
    
    def on_board_size_change(self, width, height):
        """
        Handle board size change - automatically switches model
        """
        print(f"\n{'='*40}")
        print(f"🔄 Board size changing: {self.current_width}x{self.current_height} -> {width}x{height}")
        
        # Call original method to actually change the board
        self.original_change_grid_size(width, height)
        
        # Update current size
        self.current_width = width
        self.current_height = height
        
        # Load the new model for this board size
        self.load_model_for_current_size()
        
        print(f"✅ Model switched successfully!")
        print(f"{'='*40}\n")
    
    def play(self):
        """Main game loop - AI plays automatically"""
        if not self.running:
            return
        
        # If game is over, reset automatically
        if not self.game.game_running:
            self.game.reset_game_clean()
            self.root.after(500, self.play)
            return
        
        # Get AI action (epsilon=0, pure exploitation)
        dx, dy = self.ai.get_action(self.game.snake_positions, self.game.food_position)
        
        # Execute move
        self.game.move_snake(dx, dy)
        
        # Update window title with current score
        self.root.title(f"🐍 Snake AI - Demo ({self.current_width}x{self.current_height}) | Score: {self.game.current_score}")
        
        # Schedule next move
        self.root.after(self.speed, self.play)
    
    def on_closing(self):
        """Handle window close event"""
        self.running = False
        self.root.destroy()


def list_available_models():
    """List all available trained models in pkl folder"""
    pkl_dir = "pkl"
    if not os.path.exists(pkl_dir):
        print(f"📁 No pkl folder found. No models available.")
        return []
    
    models = []
    for f in os.listdir(pkl_dir):
        if f.endswith('.pkl') and f.startswith('snake_'):
            size = f.replace('snake_', '').replace('.pkl', '')
            filepath = os.path.join(pkl_dir, f)
            size_bytes = os.path.getsize(filepath)
            models.append((size, size_bytes))
    
    return models


def main():
    parser = argparse.ArgumentParser(
        description='SnakeQL-Progressive - Test trained models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 10x10 model (default)
  python3 play.py
  
  # Run 5x5 model
  python3 play.py --size 5x5
  
  # Run 20x15 model
  python3 play.py --size 20x15
  
  # Run faster
  python3 play.py --speed 30
  
  # List available models
  python3 play.py --list
        """
    )
    
    parser.add_argument(
        '--size', '-s',
        type=str,
        default='10x10',
        help='Initial board size: 5x5, 10x10, or 20x15 (default: 10x10)'
    )
    
    parser.add_argument(
        '--speed', '-sp',
        type=int,
        default=50,
        help='Movement speed in milliseconds (default: 50, lower = faster)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available trained models'
    )
    
    args = parser.parse_args()
    
    # List models if requested
    if args.list:
        print("\n📁 Available trained models:")
        models = list_available_models()
        if models:
            for size, bytes_size in models:
                kb = bytes_size / 1024
                print(f"   🐍 {size} -> pkl/snake_{size}.pkl ({kb:.1f} KB)")
        else:
            print("   No models found. Train first using trainer.py")
        print()
        return
    
    # Parse board size
    try:
        if 'x' in args.size:
            width, height = map(int, args.size.split('x'))
        else:
            # Default presets
            presets = {
                '5x5': (5, 5),
                '10x10': (10, 10),
                '20x15': (20, 15)
            }
            if args.size in presets:
                width, height = presets[args.size]
            else:
                raise ValueError(f"Invalid size: {args.size}")
    except:
        print(f"❌ Invalid size format. Use: 5x5, 10x10, or 20x15")
        sys.exit(1)
    
    # Validate board size
    valid_sizes = [(5, 5), (10, 10), (20, 15)]
    if (width, height) not in valid_sizes:
        print(f"❌ Invalid board size. Valid sizes: 5x5, 10x10, 20x15")
        sys.exit(1)
    
    # Run demo
    demo = SnakeDemo(
        initial_width=width,
        initial_height=height,
        speed=args.speed
    )


if __name__ == "__main__":
    main()
