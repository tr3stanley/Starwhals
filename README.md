# STARWHALS

A fun 2-player battle game where you control narwhals in space! Use your horn to defeat your opponent while navigating through obstacles in various themed arenas.

![Starwhals Game](screenshot.png) *(You'll need to add a screenshot later)*

## Features

- 4 unique battle arenas with different themes and difficulty levels:
  - Training Ground: Perfect for beginners
  - Arctic Arena: Icy challenges with more obstacles
  - Deep Sea: Dark waters with many hiding spots
  - Coral Reef: Colorful and dynamic environment

- Dynamic camera system that follows the action
- Smooth physics-based movement
- Health system with visual indicators
- Beautiful particle effects and animations
- Local 2-player gameplay

## Installation

1. Make sure you have Python 3.7+ installed
2. Clone this repository:
```bash
git clone https://github.com/yourusername/starwhals.git
cd starwhals
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the game:
```bash
python starwhals.py
```

## Controls

### Player 1 (Blue Narwhal)
- A: Rotate left
- D: Rotate right
- Movement is physics-based - rotate to change direction!

### Player 2 (Pink Narwhal)
- Left Arrow: Rotate left
- Right Arrow: Rotate right
- Movement is physics-based - rotate to change direction!

### General Controls
- ESC: Return to menu
- Close window to quit

## Game Rules

1. Each player starts with 3 health points
2. Hit your opponent's body with your horn to deal damage
3. Avoid getting hit by your opponent's horn
4. Use obstacles for cover and strategic advantage
5. First player to reduce their opponent's health to zero wins!

## Requirements

- Python 3.7+
- Pygame
- NumPy

See `requirements.txt` for specific version requirements.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE) 