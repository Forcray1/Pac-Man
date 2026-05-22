*This project has been created as part of the 42 curriculum by mlorenzo, avauclai.*

---

## Description

This project is a full recreation of the classic **Pac-Man** arcade game in Python, in a point and click style, similar to the game 'Five nights at Freddy's', built with Pygame. The player navigates a procedurally generated maze, eats pac-gums, avoids (or hunts) ghosts, and progresses through multiple levels of increasing difficulty. The game features a persistent highscore system, a configuration file, a cheat mode for evaluation, a graphical main menu, and a fully polished UI.

---

## Instructions

### Installation

```bash
make install
```

This installs all dependencies using `uv`.

### Running the game

```bash
make run
```

Or manually:

```bash
python pac-man.py config.json
```

The program takes exactly one argument: a path to a JSON configuration file.

### Other rules

| Rule | Description |
|------|-------------|
| `make debug` | Run with Python's built-in debugger (`pdb`) |
| `make clean` | Remove `__pycache__`, `.mypy_cache`, `.pytest_cache`, and `.venv` |
| `make lint` | Run `flake8` and `mypy` with standard flags |
| `make lint-strict` | Run `flake8` and `mypy --strict` |

---

## Configuration

The configuration file is a standard JSON file passed as an argument on launch.
Unknown keys are ignored with a warning. Missing or invalid keys cause a clear error message and abort the launch.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `level` | int (≥ 1) | — | Number of levels in the game |
| `width` | int (≥ 3) | — | Width of the first maze |
| `height` | int (≥ 3) | — | Height of the first maze |
| `difficulty` | int (1–5) | — | Difficulty setting (see below) |
| `points_per_pacgum` | int (≥ 0) | — | Points earned per pac-gum |
| `points_per_super_pacgum` | int (≥ 0) | — | Points earned per super pac-gum |
| `points_per_ghost` | int (≥ 0) | — | Points earned per ghost eaten |
| `seed` | int | — | Seed for the first level maze (subsequent levels are random) |
| `level_max_time` | int (> 0) | — | Time limit per level in seconds |
| `cheat_mode` | bool | — | Enable or disable the cheat menu |
| `super_time` | int (≥ 0) | — | Duration (in seconds) ghosts remain frightened after a super pac-gum |
| `practice` | bool | `False` | Show ghost target paths (debug overlay) |

### Difficulty levels

| Level | Description |
|-------|-------------|
| 1 | Normal speed, fixed maze size throughout the game |
| 2 | Ghosts slightly faster than level 1 |
| 3 | Maze grows by +3 tiles each level |
| 4 | Ghosts faster, maze still grows |
| 5 | Ghosts at maximum speed, maze is re-randomized at half the time limit |

---

## Highscore System

Highscores are stored as JSON files on disk, one per difficulty level:

```
scores/1/highscores.json   ← difficulty 1
scores/2/highscores.json   ← difficulty 2
...
scores/5/highscores.json   ← difficulty 5
```

- The file is checked at startup (created with an empty list if missing).
- Top **10** scores are kept, sorted in descending order.
- Player names: max 10 characters, alphanumeric and spaces only.
- Scores: non-negative integers only.
- Players can enter their name after winning or losing a game to save their score.
- Highscores are displayed in the main menu.

This approach was chosen for simplicity, portability, and robustness: JSON is human-readable, easy to reset, and the per-difficulty separation avoids score comparison between incompatible modes.

---

## Maze Generation

Mazes are generated using the externally assigned **A-Maze-ing** package (`mazegenerator`), which is used as-is without modification. The package is located in `mazegenerator-00001-py3-none-any/` and installed as a local wheel.

- The first level always uses the fixed seed defined in `config.json`.
- All subsequent levels use a random seed (seed = 0).
- The `PERFECT` parameter is set to `False` to produce Pac-Man-compatible corridors (loops allowed).
- At difficulty 3 and above, the maze grows by +3 tiles (width and height) each level.
- At difficulty 5, the maze is re-generated mid-level when half the time limit is reached.
- A cache (`_maze_cache`) is used to make level resets instant by reusing the already-generated grid.
- The recursive `_find_short_path` method of the generator is overridden with a no-op, as it is not needed and caused exponential slowdowns on large grids.

---

## Implementation

### Game loop

The game loop lives in `core/game.py` (`Game.run()`). Each frame:
1. Events are polled (movement, pause, cheat, quit).
2. The monitor state is updated (entity positions, collisions, super-pacgum timer).
3. Win/lose/time-up conditions are checked.
4. If the player is dying, a death animation timer runs before resetting.
5. The frame is rendered via `PygameViewer.render_frame()`.

### Death & time-up

Both ghost kills and time expiration trigger `player.die()`, which sets `is_dying = True`. A `death_timer` counts 40 frames (~1.3 s at 30 FPS) before resetting the level — ensuring the death animation always plays regardless of cause. A `time_up` flag ensures `elapsed` is reset to 0 after a time-up death.

### Input freeze on level start

At the start of each level (and after each respawn), all pygame events are blocked for 2 seconds using `pygame.event.set_blocked(None)`, then re-enabled with `pygame.event.set_allowed(None)`. A final `pygame.event.pump()` + `pygame.event.clear()` flushes any OS-buffered events before re-enabling input.

### Ghost AI

Each ghost extends the abstract `Ghost` class and overrides `choose_target()`:

| Ghost | Behaviour |
|-------|-----------|
| **Blinky** | Direct chase — always targets Pac-Man's exact position |
| **Pinky** | Ambush — targets 4 cells ahead of Pac-Man's direction |
| **Inky** | Flanking — reflects Blinky's position through 2 cells ahead of Pac-Man |
| **Clyde** | Shy — chases when >8 tiles away, retreats to his corner when close |

In frightened mode, all ghosts move randomly and avoid 180° turns. Ghosts cannot make U-turns except when no other option exists. Blinky accelerates (Elroy mode) once 75% and 90% of pac-gums have been eaten.

### Cheat mode

Accessible via `C` during the game (if `cheat_mode` is enabled in the config). Available cheats:
- **God mode** (`G` key): Pac-Man becomes invincible.
- **Next level** (via cheat menu): Skip to the next level instantly.
- **Ghost freeze** (via cheat menu): Stop all ghost movement.
- **Extra life** (via cheat menu): Add a life to the player.

---

## General Software Architecture

```
pac-man.py          Entry point — parses args, calls parser, launches Redirect
core/
  parser.py         JSON config parsing and validation
  config.py         In-game config editor (CRT-style UI)
  redirect.py       Hub / main menu screen, transitions between views
  game.py           Per-level game loop (input, state, win/lose logic)
  monitor.py        Central game state (grid, player, ghosts, items)
  scores.py         Highscore persistence (load, save, top-10 management)
entities/
  entity.py         Base class for all moving entities
  player.py         PacMan — movement, lives, score, power state
  ghost.py          Abstract Ghost — shared AI logic, movement, frightened mode
  ghost_types.py    Blinky, Pinky, Inky, Clyde — each overrides choose_target()
  items.py          Pacgum, SuperPacgum
display/
  pygame_viewer.py  PygameViewer — assembles mixins, owns screen & game flow
  renderer_mixin.py All draw calls (maze, sprites, walls, HUD)
  hud_mixin.py      In-game HUD (score, lives, level, timer)
  screens_mixin.py  Full-screen UI loops (menu, highscores, instructions, end)
  sprite_mixin.py   Sprite loading, scaling, animation frame management
  screen.py         CRT power-on animation helper
  _maze_utils.py    Maze generator wrapper + cache
animation/          WebP animation frames (intro, transitions)
assets/             Sprite sheets, maze tiles, wall tiles
config/config.json  Default configuration file
scores/             Per-difficulty highscore JSON files
```

**Key design choices:**
- `PygameViewer` is composed from four mixins (`RendererMixin`, `HudMixin`, `ScreensMixin`, `SpritesMixin`) to keep each concern in its own file.
- `Monitor` is the single source of truth for game state; neither the renderer nor the game loop mutate entities directly without going through it.
- `Ghost` is abstract (`ABC`); each ghost type only needs to implement `choose_target()`, sharing all movement, collision, and frightened logic.

---

## Project Management

The project was managed jointly by **mlorenzo** and **avauclai**.

### Brief overview

| Period | Focus |
|--------|-------|
| 06–08/05 | Architecture decisions, entity classes, ghost AI, parser |
| 09–11/05 | Pygame viewer, ghost integration, menu, scoring |
| 12–14/05 | Sprite system, animations, level progression, cheat mode |
| 15–21/05 | Pause menu, fullscreen, config editor, flake8/mypy compliance |
| 22–[final date]/05 | Final polish, README, packaging, bug fixes |

---

## Resources

- [Pac-Man Wiki — Ghost AI](https://aighost.co.uk/how-pac-man-ghost-ai-works-the-classic-chase-algorithms/)
- [Pac-Man Fandom Wiki](https://pacman.fandom.com/wiki/Pac-Man_Wiki)
- [Pygame documentation](https://www.pygame.org/docs/)
- [Advanced OpenGL in Python with Pygame](https://stackabuse.com/advanced-opengl-in-python-with-pygame-and-pyopengl/)
- [Play classic Pac-Man](https://pacman.live/play.html)

### AI usage

AI was used throughout this project for:
- Accelerating boilerplate code (mixins structure, type hints, docstrings).
- Help with this README structure.

All AI-generated content was reviewed, understood, tested, and adapted by the team before being committed.

---

## Config File

- "level": Numbers of levels
- "width": Width of the first maze
- "height": Height of the first maze
- "difficulty": Difficulty from 1 to 5:
	- 1: No buffs on the ghosts, and the maze size stay still throughout the game
	- 2: Ghosts are a bit faster than level 1
	- 3: Maze is increasing in size at each level
	- 4: Ghosts are faster than level 3
	- 5: Ghosts are at theire fastest, and the maze is randomized when half of the max time is remaining
- "points_per_pacgum": Points earned for each PacGum
- "points_per_super_pacgum": Points earned for each Super-PacGum
- "points_per_ghost": Points earned for each Ghost eaten
- "seed": Preset seed for the first level
- "level_max_time": max time for each level
- "cheat_mod": cheat mod for the review
- "display_mode": 1 or 2
	- 1: Basic ascii representation of the classic pacman
	- 2: Graphical interface, with the full game


## Ressources :
* https://stackabuse.com/advanced-opengl-in-python-with-pygame-and-pyopengl/
* https://pacman.fandom.com/wiki/Pac-Man_Wiki
* https://pacman.live/play.html
* https://aighost.co.uk/how-pac-man-ghost-ai-works-the-classic-chase-algorithms/

```
Timeline :
06/05/2026 :
	Beginning of the project, Major decision about game options and theme sets together
	avauclai:
		organization of the structure of the projet, implementation of entity class and player class
	mlorenzo:
		decomposition of the project and major points to organize set, implementation of the ghost classes prototypes
07/05/2026 :
	avauclai :
		- Sprite Cutting : Creating and cutting the different assets.
		- Gameplay Mechanics: We updated the player logic (player.py) so that Pac-Man slightly slows down while eating pac-gums, accurately replicating the classic game's behavior.
		- Terminal UI Fixes: We fixed the screen flickering and input lag during terminal gameplay (ascii_viewer.py) by disabling mouse event capturing in the curses engine. 
	mlorenzo :
		- Monitor class added to keep track of all the instances of the game at one place
		- Added an edited version of viewer_ascii.py to match the monitor.py, not much change to it mostly reorganisation to ease further progress
		- Ghost class fully implemented except draw
		- Chase from each ghost type implemented :
			Blinky (red): direct chase — always targets Pac-Man's exact position.
			Pinky (pink): ambush — targets 4 cells ahead of Pac-Man's direction; falls back to direct chase if blocked.
			Inky (blue): flanking — targets the reflection of Blinky's position through 2 cells ahead of Pac-Man; most unpredictable.
			Clyde (orange): shy — chases when more than 8 tiles away, retreats to his spawn corner when close.
		- No tests nor debugging and implementation not done to the game yet
08/05/2026 :
	avauclai :
		- Integrated the ghost on the terminal
	mlorenzo :
		- Perfected Ghosts classes, added a choose_target_frighten to move randomly according to the real game, and a direction for sprites and avoidance of 180 degree turns
		- Edited Inky to make him fall to direct chase if Blinky dies, so that he doesn't become static
		- Did the parser and did the default config.json, still need to test it
		- Cleaned the project for flake8 and mypy before going further
09/05/2026 :
	avauclai :
		- Terminal Prototyping: Developed a curses interface for real-time maze configuration and entry/exit point placement.
        _ Telemetry Dashboard: Added a real-time debug overlay in the terminal to monitor ghost targets, positions, and active modes.
        - UI Development: Created a 90s Windows-style main menu in Pygame featuring beveled buttons and a teal aesthetic.
        - Transition Effects: Implemented a cinematic fade-to-black system to handle smooth loading between the menu and the game.
        -3D Integration: Prepared the engine to display high-quality pre-rendered 3D scenes created in Blender.
	mlorenzo : 
		- Upgrade for U turns, generalized it in possible moove, with a fallback to U turn if no other possibility
		- Implementation of the Elroy mode for blinky in monitor, for him to accelerate once 75% and 90% of the totals pacgums have been eaten
		- Parser implemented to the program, and setup the main to launch as the subject requiered
11/05/2026 : 
	avauclai : 
		- Successfully developed a fully functional Pygame-based Pac-Man interface featuring seamless maze wall rendering, A*-driven ghost AI, collectible items, and smooth movement interpolation optimized for cross-device compatibility.
        - We analyzed the maze generator and found that while the generation is efficient, the solving algorithm (IDDFS with backtracking) has exponential time complexity ($O(b^d)$), causing the execution time to explode from 90 seconds for a $26 \times 26$ grid to an estimated 2.5 days for a $30 \times 30$ grid—a problem that can be solved by switching to a linear-time Breadth-First Search (BFS).
	mlorenzo :
		- implementation of a U turn if a ghost is closer than 5 blocks when pacman eat a super pacgum
		- Basic menu implemented, wich give the possibility between instruction, exit, scores, and play the game
		- Added the game over screen, and the win screen, wich both give the possibility to save the scores in the respective file setup in the config
		- Added the scores implementation, wich give the possibility to access, change and add scores, and change automatically the score if 10 are already presents, and the new one is higher than the 10th.
		- Cleaned parts of the projects for flake8 and mypy
12/05/2026 :
	avauclai :
		- I continued to create the 3D Blender rendering, created the animations, and understood the file compression constraints. 
	mlorenzo
		- Adaptation of the code done to flake8
		- Added verifs to the scores entry to avoid None, boolean, and negative integers
		- Correction of the bug making the respawn impossible, so respawn for as long as you have life is working
		- Added a two second cooldown when the game start and reset
		- Reorganisation of the project to put everything in dedicated files
		- Modified the maze generation algorithm used in the programm to supress the negative points of the recursive usage in the given package: 
			- Added a cache for reset levels to be instant
			- Override the _find_short_path to a pass because we don't use it and so it just slowed the process
		- Added specific files for each difficulty highscores
13/05/2026 :
	avauclai :
		- The Pacgums weren’t spawning in the corners, probably because of the position of the ghosts, so I fixed it.
		- We have noticed that the walls without any squares of other surrounding walls were treated as empty squares. So to fix it, I filled these walls with a rectangle the width of the walls
14/05/2026:
	avauclai:
		- Animation on the launch screen
		- Creation of the GodMod
		- Implementation of the level system.
		- We have become aware of the challenge related to the weight/quality ratio of animation images, which is imposed by the Git of 42.
		- I have finished the main piece without animation of the 3D render.
15/05/2026:
	avauclai:
		- We understood that the most suitable format was WebP, compress to 100%. We are still thinking about how to integrate the image volume on the git in the most intelligent way possible.
		- Start of animations (BaseAnimation, TransitionToArcade) stored on a drive
		- removal of ASCII mode 
	mlorenzo :
		- Added the current level to the game window
		- Edited the scores file storqge, to have a specialized files for each difficulty level
		- Made the win screen working by adding "level" to the config of monitor
		- Reorganization of the pygame_viewer in multiples files for better understanding
		- Added the augmentation of the size of the maze for the difficulty 3 and above (+3 for difficulty 3 and 4, and +6 for difficulty 5)
19/05/2026:
	mlorenzo:
		- Pause menu implemented
21/05/2026:
	mlorenzo:
		- Cheat menu fully implemented
		- Reorganisation to put game logic in game.py
		- All cheats implemented, and staying on throughout the levels
		- Added the reroll of the maze when half of the requiered time is used at level 5
		- Adapted the project to respect mypy and flake8
		- Small Re design of the pause and cheat window
		- Corrected some incoherences between the code and the subject, such as the cheat menu when cheatmod off, or points_per_ghosts partially ignored
22/05/2026:
	mlorenzo:
		- Edited the windows to be full screen at all time
		- Did the config.py wich will contain the edit of the config throughout the computer of the Hub of the game
		- Edits to pass through flake8 and mypy without any issues
		- Added dynamiic size to text, so that it fill the screen entirely and not only the base text
		- Finished all the game, missing only the animations and the debugg, and some re-design
		- Perfected parsing with files verifs, and warning for unknown key(s)
		- Instructions were stackable during the freeze at the start of each level, corrected by clearing the events at the end of the time sleep in pygame_viewer.py
```

# Edits since last commit:
Le jeu est finito

# Edit a faire : 
refaire le visuel des menus pause et cheat
refaire le menu de start de pacman
cacher les hitboxs
rajouter toutes les animations
faire README
faire packages itch.io
debugg
Ajouter date de fin de projet dans le README, a la place du '[final date]'

j'ai trouver un bug que j'arrive pas a corriger, si tu spam 'c' quand tu respawn ca bug, mais si tu coupe et clear pas les instructions, elles se stacks les une sur les autres, si tu trovue comment le corriger ca m'arrange sinon nsm