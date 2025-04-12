# Starwhals Development Notes

## Project Overview
Starwhals is a 2-player battle game where players control narwhals in space, trying to defeat each other while navigating through various themed arenas.

## Repository Information
- GitHub Repository: https://github.com/tr3stanley/Starwhals
- Main Branch: main
- Primary Game File: starwhals.py

## Recent Changes (2024-04-12)
1. Added home screen with level selection
2. Implemented multiple game levels:
   - Training Ground
   - Arctic Arena
   - Deep Sea
   - Coral Reef
3. Created proper project structure with:
   - README.md
   - requirements.txt
   - LICENSE (MIT)
   - .gitignore

## Git Commands Reference
Common commands used in this project:

```bash
# Initialize repository
git init

# Add files
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push -u origin main

# Pull latest changes
git pull origin main

# Clone repository (for new machines)
git clone https://github.com/tr3stanley/Starwhals.git
```

## Project Structure
```
Starwhals/
├── starwhals.py          # Main game file
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── LICENSE              # MIT License
├── .gitignore          # Git ignore rules
└── DEVELOPMENT.md      # Development notes (this file)
```

## Dependencies
- Python 3.7+
- Pygame >= 2.5.0
- NumPy >= 1.24.0

## Future Improvements
1. Game Features
   - [ ] Add power-ups
   - [ ] Implement particle effects
   - [ ] Add sound effects and background music
   - [ ] Create more levels with unique mechanics
   - [ ] Add customizable narwhal skins

2. Technical Improvements
   - [ ] Optimize collision detection
   - [ ] Add configuration file for game settings
   - [ ] Implement save/load game state
   - [ ] Add proper logging system

3. Documentation
   - [ ] Add screenshots to README
   - [ ] Create contribution guidelines
   - [ ] Add code documentation
   - [ ] Create wiki pages

## Development Environment Setup
1. Clone the repository
```bash
git clone https://github.com/tr3stanley/Starwhals.git
cd Starwhals
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the game
```bash
python starwhals.py
```

## Useful Resources
- [Pygame Documentation](https://www.pygame.org/docs/)
- [NumPy Documentation](https://numpy.org/doc/)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)

## Notes
- The game uses a dynamic camera system that follows both players
- Physics system includes momentum and realistic collisions
- Level generation is procedural with configurable parameters

## Troubleshooting
Common issues and solutions:

1. Git Line Ending Warnings
   - These are normal on Windows systems
   - Can be fixed with: `git config --global core.autocrlf true`

2. Git Authentication
   - Use GitHub's web interface for authentication
   - Token-based authentication is recommended for security

## Contact
- GitHub: @tr3stanley
- Email: tr3stanley34@gmail.com 