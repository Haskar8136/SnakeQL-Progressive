#!/bin/bash

# ============================================
# SnakeQL-Progressive - Launch Script
# ============================================
# This script launches the Snake AI Trainer or Demo Mode
# with automatic environment setup
# ============================================

# Colors for terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================
# FUNCTIONS
# ============================================

show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo -e "║     🐍 ${WHITE}SnakeQL-Progressive${CYAN} - Q-Learning Snake AI Trainer                 ║"
    echo "║                                                                              ║"
    echo -e "║     ${GREEN}Pure Q-Learning tabular that actually scales to 10x10${CYAN}               ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_menu() {
    echo -e "${YELLOW}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│                        🎮 MAIN MENU                             │"
    echo "├─────────────────────────────────────────────────────────────────┤"
    echo -e "│ ${GREEN}1${NC}) ${WHITE}▶ Train Model${NC}                                                  │"
    echo -e "│ ${GREEN}2${NC}) ${WHITE}🎮 Test Model (Demo Mode)${NC}                                       │"
    echo -e "│ ${GREEN}3${NC}) ${WHITE}📋 List Available Models${NC}                                        │"
    echo -e "│ ${GREEN}4${NC}) ${WHITE}🗑️  Clean Models (Delete PKL)${NC}                                  │"
    echo -e "│ ${GREEN}5${NC}) ${WHITE}📊 View Model Statistics${NC}                                        │"
    echo -e "│ ${GREEN}6${NC}) ${WHITE}⚙️  Settings${NC}                                                  │"
    echo -e "│ ${RED}0${NC}) ${WHITE}❌ Exit${NC}                                                          │"
    echo "└─────────────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

check_python() {
    echo -e "${YELLOW}📌 Checking Python...${NC}"
    python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
    
    if [ -z "$python_version" ]; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Python $python_version detected${NC}"
    
    # Check if Python 3.8+
    if (( $(echo "$python_version < 3.8" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${RED}❌ Python 3.8+ is required. Current version: $python_version${NC}"
        return 1
    fi
    
    return 0
}

check_packages() {
    echo -e "${YELLOW}📌 Checking required packages...${NC}"
    
    MISSING_PACKAGES=()
    
    # Check tkinter
    python3 -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        MISSING_PACKAGES+=("tkinter")
    fi
    
    # Check matplotlib
    python3 -c "import matplotlib" 2>/dev/null
    if [ $? -ne 0 ]; then
        MISSING_PACKAGES+=("matplotlib")
    fi
    
    # Check numpy
    python3 -c "import numpy" 2>/dev/null
    if [ $? -ne 0 ]; then
        MISSING_PACKAGES+=("numpy")
    fi
    
    if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
        echo -e "${RED}❌ Missing packages: ${MISSING_PACKAGES[*]}${NC}"
        echo -e "${YELLOW}📌 Install with: pip3 install ${MISSING_PACKAGES[*]}${NC}"
        
        # Offer to install
        read -p "Do you want to install missing packages? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for package in "${MISSING_PACKAGES[@]}"; do
                if [ "$package" == "tkinter" ]; then
                    echo -e "${YELLOW}📌 Installing python3-tk...${NC}"
                    sudo apt-get install -y python3-tk 2>/dev/null || \
                    sudo pacman -S tk 2>/dev/null || \
                    echo -e "${RED}⚠️ Could not install tkinter automatically${NC}"
                else
                    pip3 install "$package"
                fi
            done
        else
            echo -e "${RED}❌ Cannot continue without required packages.${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}✅ All required packages are installed${NC}"
    return 0
}

create_folders() {
    echo -e "${YELLOW}📌 Creating necessary folders...${NC}"
    mkdir -p pkl
    mkdir -p logs
    echo -e "${GREEN}✅ Folders ready (pkl/, logs/)${NC}"
}

check_files() {
    echo -e "${YELLOW}📌 Checking project files...${NC}"
    
    FILES=("interface.py" "hybrid_snake.py" "trainer.py" "play.py")
    MISSING=0
    
    for file in "${FILES[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ Missing: $file${NC}"
            MISSING=1
        fi
    done
    
    if [ $MISSING -eq 1 ]; then
        echo -e "${RED}❌ Missing required files. Check your installation.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ All files found${NC}"
    return 0
}

show_models() {
    echo -e "${YELLOW}📌 Available trained models:${NC}"
    
    if [ -d "pkl" ]; then
        models=$(ls -la pkl/*.pkl 2>/dev/null | wc -l)
        if [ $models -gt 0 ]; then
            echo ""
            ls -la pkl/*.pkl 2>/dev/null | awk '{print "   📁 " $9 " (" $5 " bytes)"}'
            echo ""
        else
            echo -e "   ${YELLOW}📁 No trained models found${NC}"
        fi
    else
        echo -e "   ${YELLOW}📁 No trained models found${NC}"
    fi
}

train_model() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║     🚀 Launching Snake AI Trainer...                         ║"
    echo "║                                                              ║"
    echo "║     The trainer window will open.                            ║"
    echo "║     Close the window to return to menu.                      ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    python3 trainer.py
    
    echo -e "${GREEN}✅ Trainer closed.${NC}"
    read -p "Press Enter to continue..."
}

demo_mode() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║     🎮 Demo Mode - Testing trained model                     ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Show available models
    show_models
    
    echo ""
    echo -e "${YELLOW}Select board size:${NC}"
    echo -e "  ${GREEN}1${NC}) 5x5"
    echo -e "  ${GREEN}2${NC}) 10x10"
    echo -e "  ${GREEN}3${NC}) 20x15"
    echo -e "  ${RED}0${NC}) Cancel"
    echo ""
    read -p "Option: " demo_option
    
    case $demo_option in
        1)
            python3 play.py --size 5x5
            ;;
        2)
            python3 play.py --size 10x10
            ;;
        3)
            python3 play.py --size 20x15
            ;;
        *)
            echo -e "${YELLOW}Cancelling...${NC}"
            return
            ;;
    esac
    
    read -p "Press Enter to continue..."
}

list_models() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    📋 AVAILABLE MODELS                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    if [ -d "pkl" ]; then
        models=$(ls pkl/*.pkl 2>/dev/null)
        if [ -n "$models" ]; then
            for model in $models; do
                name=$(basename "$model")
                size=$(stat -c%s "$model" 2>/dev/null || stat -f%z "$model" 2>/dev/null)
                kb=$((size / 1024))
                echo -e "   🐍 ${WHITE}$name${NC} - ${kb} KB"
                
                # Try to read basic model stats
                if [ -f "read_stats.py" ]; then
                    python3 read_stats.py "$model" 2>/dev/null
                fi
            done
        else
            echo -e "   ${YELLOW}📁 No trained models found${NC}"
            echo ""
            echo -e "   To train a model, select option 1 from the main menu."
        fi
    else
        echo -e "   ${YELLOW}📁 No trained models found${NC}"
        echo ""
        echo -e "   To train a model, select option 1 from the main menu."
    fi
    
    echo ""
    read -p "Press Enter to continue..."
}

clean_models() {
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🗑️ CLEAN MODELS                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    if [ -d "pkl" ] && [ "$(ls -A pkl/*.pkl 2>/dev/null)" ]; then
        show_models
        echo ""
        read -p "Are you sure you want to delete ALL models? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f pkl/*.pkl
            echo -e "${GREEN}✅ All models have been deleted.${NC}"
        else
            echo -e "${YELLOW}Operation cancelled.${NC}"
        fi
    else
        echo -e "${YELLOW}No models to delete.${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

view_stats() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    📊 MODEL STATISTICS                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    show_models
    
    if [ -d "pkl" ] && [ "$(ls -A pkl/*.pkl 2>/dev/null)" ]; then
        echo ""
        read -p "Enter model size (e.g., 10x10): " size_stats
        
        if [ -f "pkl/snake_${size_stats}.pkl" ]; then
            python3 -c "
import pickle
import os

filename = 'pkl/snake_${size_stats}.pkl'
if os.path.exists(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    
    print(f'\n📊 Statistics for {size_stats} model:')
    print(f'   📚 Q-Table: {len(data.get(\"q_table\", {}))} states')
    print(f'   🎯 Episodes: {data.get(\"episodes\", 0)}')
    print(f'   🏆 Best score: {data.get(\"best_score\", 0)}')
    print(f'   🔍 Epsilon: {data.get(\"epsilon\", 1.0):.4f}')
    print(f'   ✅ Valid episodes: {len(data.get(\"valid_scores\", []))}')
    print(f'   🗑️ Discarded: {data.get(\"discarded\", 0)}')
    
    scores = data.get('valid_scores', [])
    if scores:
        avg = sum(scores[-100:]) / min(len(scores), 100)
        print(f'   📈 Average (last 100): {avg:.1f}')
"
        else
            echo -e "${RED}No model found for ${size_stats}${NC}"
        fi
    fi
    
    read -p "Press Enter to continue..."
}

settings() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ⚙️ SETTINGS                                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${YELLOW}Current configuration:${NC}"
    echo "   📁 Models folder: pkl/"
    echo "   🐍 Python: $(python3 --version)"
    echo ""
    
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  ${GREEN}1${NC}) Check dependencies again"
    echo -e "  ${GREEN}2${NC}) Install missing dependencies"
    echo -e "  ${RED}0${NC}) Back"
    echo ""
    
    read -p "Option: " settings_option
    
    case $settings_option in
        1)
            check_packages
            ;;
        2)
            pip3 install numpy matplotlib
            sudo apt-get install -y python3-tk 2>/dev/null || sudo pacman -S tk 2>/dev/null
            echo -e "${GREEN}✅ Installation completed${NC}"
            ;;
        *)
            return
            ;;
    esac
    
    read -p "Press Enter to continue..."
}

# ============================================
# MAIN
# ============================================

# Clear screen
clear

# Show banner
show_banner

# Check environment
check_python
if [ $? -ne 0 ]; then
    exit 1
fi

check_packages
if [ $? -ne 0 ]; then
    exit 1
fi

create_folders
check_files
if [ $? -ne 0 ]; then
    exit 1
fi

# Main loop
while true; do
    clear
    show_banner
    show_menu
    
    read -p "Select an option: " option
    
    case $option in
        1)
            train_model
            ;;
        2)
            demo_mode
            ;;
        3)
            list_models
            ;;
        4)
            clean_models
            ;;
        5)
            view_stats
            ;;
        6)
            settings
            ;;
        0)
            echo -e "${GREEN}Thanks for using SnakeQL-Progressive! 🐍${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option.${NC}"
            sleep 1
            ;;
    esac
done
