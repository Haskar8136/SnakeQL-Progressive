# 🐍 SnakeQL-Progressive

## Pure Q-Learning tabular that reaches 290 points on 10x10. No DQN. No Hamiltonians. Just patience and progressive filtering.

Most people say Q-Learning tabular doesn't scale beyond simple grids. This project proves them wrong.

---

## 🔥 Key Results

| Metric | Value |
|--------|-------|
| **Best Score** | 290 points (29 apples) |
| **Average** | 145+ points |
| **Q-Table Size** | 2,777 states |
| **Board** | 10x10 |
| **Training Time** | Days (not hours) |

---

## 💡 The Innovation: Progressive Filtering (50% Rule)

Most implementations use a fixed filter. This project uses **progressive filtering**:

| Stage | Cleanup Threshold (remove from PKL) | Entry Threshold (new episodes) | Ratio |
|-------|-------------------------------------|--------------------------------|-------|
| Day 1 | 110 | 55 | 50% |
| Day 2 | 150 | 75 | 50% |
| Day 3 | 200 | 100 | 50% |
| Day 4 | 250 | 125 | 50% |

```python

# Example configuration
CLEANUP_THRESHOLD = 150  # Episodes <150 removed from PKL
ENTRY_THRESHOLD = 75     # New episodes <75 never enter PKL

```
Why this works: The agent needs SPACE TO FAIL. If you only allow perfect episodes, the agent never learns. By keeping entry threshold at 50% of cleanup threshold, the agent can experiment with "normal" episodes while the PKL only stores quality experiences.

## 🧠 How It Works

Architecture

    Pure Q-Learning tabular (no neural networks, no DQN)

    4 Strategies: AGGRESSIVE, BALANCED, SAFE, EXPLORE

    12 Manoeuvres: 3 per strategy (TOWARD_FOOD, FOLLOW_WALL, FOLLOW_TAIL, RANDOM, etc.)

    State: 8 dimensions (food direction, danger code, snake length, free space, etc.)

Training Pipeline

    Train for DAYS (this is the secret - most researchers stop after hours)

    Progressive cleanup - raise thresholds as agent improves

    Manual cleanup button to remove low-quality episodes from PKL

    One PKL per board size (5x5, 10x10, 20x15) 

🎮 Features

    ✅ Pure Q-Learning (no neural networks, no DQN)

    ✅ Progressive filtering (innovative - not documented elsewhere)

    ✅ Manual cleanup of low-quality episodes from PKL

    ✅ One PKL per board size (5x5, 10x10, 20x15)

    ✅ Live training visualization with matplotlib

    ✅ Strategy + manoeuvre system (12 actions total)

    ✅ Stuck penalty (prevents inactivity)

    ✅ Starvation penalty (prevents infinite loops)

    ✅ Multi-board support (5x5, 10x10, 20x15)

## 🏆 Current Records

Board	Total Cells	Best Score	% of Board	Status

5x5  25  50  100%	Complete
10x10  100  290  29%	In progress
20x15  300	-	-  Future work

## 📂 Project Structure
```
SnakeQL-Progressive/
├── hybrid_snake.py      # Q-Learning algorithm (12 strategies+manoeuvres)
├── interfaz.py          # Game GUI with visual effects
├── trainer.py           # Training with progressive filtering
├── snake_5x5.pkl        # Trained model for 5x5
├── snake_10x10.pkl      # Trained model for 10x10
└── snake_20x15.pkl      # Trained model for 20x15 (in progress)

```
🚀 How to Use
main menu, training & try out model
```bash

# make it executable
chmod +x run.sh
# run it
./run.sh

```
    Use the green slider to set ENTRY threshold

    Use the red slider to set CLEANUP threshold

    Click "ELIMINAR EPISODIOS BAJOS AHORA" to clean the PKL

    Let it run for DAYS for best results

Key insights from this project:

    Space to fail - Entry threshold at 50% of cleanup threshold

    Progressive cleaning - Raise thresholds as agent improves

    Patience - Days of training, not hours

    Manual control - You decide when to clean the PKL

## 🤝 Contributing

This project demonstrates that Q-Learning tabular is more powerful than commonly believed. If you want to try reaching 500 points, feel free to:

    Fork the repository

    Train for several days with progressive filtering

    Share your results!

## ⭐ Show Your Support

If you appreciate pure Q-Learning and the patience it takes to train for days, give this project a star.

No DQN. No Hamiltonians. No shortcuts. Just Q-Learning and time.

## 📝 License

MIT License - Feel free to use, modify, and share.

Made with 🐍 and days of patience.

