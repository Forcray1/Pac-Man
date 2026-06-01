*This project has been created as part of the 42 curriculum by mlorenzo, avauclai.*

---

## Description

This project is a full recreation of the classic **Pac-Man** arcade game in Python, wrapped in a point-and-click presentation inspired by *Five Nights at Freddy's*. The game is launched into a **hub screen** (a workshop scene) where the player clicks the **arcade cabinet** to play, the **retro computer** to edit the configuration, or the **fan** to toggle the ambient animation. Each entry plays a transition animation, a contextual **achievement-style helper popup** introduces the screen's controls, and a CRT-style editor lets the player tweak the JSON config without leaving the game.

Once inside the arcade, the player navigates a procedurally generated maze, eats pac-gums, avoids (or hunts) ghosts, and progresses through configurable difficulty modes. The game includes a persistent highscore system, a robust JSON-with-comments config parser, a cheat mode for evaluation, a polished fullscreen UI, and sound effects.

---

## Instructions

### Requirements

- Python 3.10+
- [`uv`]
- All Python dependencies are declared in `pyproject.toml` (pygame, the assigned A-Maze-ing wheel, etc.)

### Installation

```bash
make install
```

This runs `uv sync`, which creates a virtualenv in `.venv/` and installs every dependency, including the assigned `mazegenerator-00001-py3-none-any.whl` wheel.

### Running the game

```bash
make run
```

Or, equivalently:

```bash
uv run python pac-man.py config.json
```

The program takes **exactly one argument**: the *name* of a JSON file located inside the `config/` directory. Any other invocation (missing argument, non-JSON file, missing file, malformed JSON) is caught and reported with a clear message — never a Python traceback.

### Controls

| Context | Input |
|---------|-------|
| **Lobby (hub screen)** | Mouse — click the arcade cabinet / computer / fan / quit button |
| **Game** | Arrow keys *or* WASD |
| **Pause** | `ESC` to open the pause menu |
| **Cheat menu** | `C` during the game (only if `cheat_mode` is enabled) |
| **Arcade menu / highscores / instructions** | Mouse hover + click, or arrow keys + `ENTER` |
| **Config editor** | `UP/DOWN` to navigate, `ENTER` to edit, `ESC` to exit |

### Other Makefile rules

| Rule | Description |
|------|-------------|
| `make debug` | Run with Python's built-in debugger (`pdb`) |
| `make clean` | Remove `.venv`, `build/`, `dist/`, `__pycache__`, `.mypy_cache`, `.pytest_cache` |
| `make lint` | Run `flake8` and `mypy` with the project's standard flags |
| `make lint-strict` | Run `flake8` and `mypy --strict` |
| `make package` | Build the standalone game bundle with PyInstaller |

---

## Configuration

The config file is a standard JSON file with **comment support**: any line whose first non-whitespace character is `#`, or anything after `//` on a line, is stripped before parsing. Unknown keys are dropped with a warning; missing or out-of-range keys fall back to the safe defaults below (also with a warning). The launch **never aborts** on a recoverable config issue.

| Key | Type | Range | Default | Description |
|-----|------|-------|---------|-------------|
| `level` | int | 1–999 | `1` | Number of levels to play through before the win screen |
| `width` | int | 3–50 | `15` | Width of the *first* maze (in cells) |
| `height` | int | 3–50 | `15` | Height of the *first* maze (in cells) |
| `difficulty` | int | 1–5 | `1` | Difficulty preset (see below) |
| `points_per_pacgum` | int | 0–999 | `10` | Points granted per pac-gum eaten |
| `points_per_super_pacgum` | int | 0–999 | `50` | Points granted per super pac-gum eaten |
| `points_per_ghost` | int | 0–999 | `200` | Points granted per edible ghost eaten |
| `seed` | int | any | `42` | Seed used for the **first** level (subsequent levels are random) |
| `level_max_time` | int | 1–999 | `90` | Time limit per level, in seconds |
| `cheat_mode` | bool / `"True"` / `"False"` | — | `False` | Enable in-game cheat menu (peer-review tool) |
| `super_time` | int | 0–999 | `8` | Duration in seconds ghosts stay frightened after a super pac-gum |
| `practice` | bool / `"True"` / `"False"` | — | `False` | Debug overlay: draws each ghost's planned path |

The parser also injects a derived `highscore_filename` key (see *Highscore*).

### Difficulty levels

| Level | Behaviour |
|-------|-----------|
| **1** | Baseline — ghosts at normal speed, maze size fixed for every level |
| **2** | Ghosts slightly faster than level 1 |
| **3** | Ghosts speed kept, maze grows by +3 tiles in width and height every level |
| **4** | Ghosts faster, maze still grows |
| **5** | Ghosts at max speed, maze is **re-randomized in place** when half of `level_max_time` has elapsed |

---

## Highscore

Highscores are persisted as a **JSON array on disk**, with one file per difficulty:

```
scores/1/highscores.json   ← difficulty 1
scores/2/highscores.json   ← difficulty 2
...
scores/5/highscores.json   ← difficulty 5
```

The parser ensures the correct file for the active difficulty exists at startup (creates it as an empty list if missing) and aborts gracefully if it cannot be created. At game-end the score manager loads the file, drops malformed entries, validates the player's name (max 10 characters, alphanumeric + spaces only) and score (non-negative integer), inserts the new entry, sorts descending, and trims to the top 10 before writing back.

**Why per-difficulty files?** Difficulty changes the ghost speed, the maze growth rate, and (at level 5) re-rolls the maze mid-game. Mixing those scores into a single board would not be meaningful — a score earned in difficulty 1 is not comparable to one earned in difficulty 5. Splitting the files also makes the board easy to reset for a single difficulty without losing the others.

**Why JSON on disk rather than a database?** JSON is human-readable, trivially diffable in git, requires no external service, and survives unzipping the packaged build. The score manager treats every read as untrusted: any non-dict entry, missing key, wrong type, or out-of-bounds value is filtered out instead of crashing.

The top 10 is displayed via the arcade's *View Highscores* menu, and the player is prompted for a name on every win or loss before being returned to the arcade menu.

---

## Maze Generation

Mazes are generated using the externally assigned **A-Maze-ing** package (`mazegenerator-00001-py3-none-any.whl`), which is installed as a local wheel and used **as-is, without modification**.

- The first level always uses the fixed seed defined in `config.json` (`42` by default).
- All subsequent levels pass `seed = 0`, which the generator interprets as "random".
- `PERFECT` is set to `False` so the generator emits Pac-Man-compatible corridors (loops allowed, no dead-end tree).
- At **difficulty 3+**, the maze grows by +3 cells in width and height between levels.
- At **difficulty 5**, the maze is re-generated in place when half of `level_max_time` remains, preserving the player's score and lives.
- A `_maze_cache` keyed on `(seed, width, height)` makes level resets (death, respawn) instantaneous by reusing the already-generated grid.
- The generator's recursive `_find_short_path` method is monkey-patched to a no-op at startup — it is unused by our game and caused exponential slowdowns on large grids without that override. The generator itself is otherwise untouched.
- If the generator raises, the loader catches the exception, prints a clean error, and exits without a traceback.

---

## Implementation

### Entry point

`pac-man.py` validates its single CLI argument, smoke-tests the maze generator with a small grid, parses the config, then hands off to `Redirect.main_menu()` which owns the hub loop and dispatches to the arcade or the config editor.

### Hub / lobby

`core/redirect.py` runs the workshop scene. Each interactive element is a polygon (arcade cabinet, retro computer, fan base) hit-tested with a ray-casting algorithm on the mouse position. Clicking an element plays a transition animation (forward when entering, reversed when returning) and reuses the same pygame surface across transitions to avoid flicker. The fan polygon toggles a slow-down/spin-up state machine that drives both the background animation FPS and the ambient fan-noise volume in lock-step.

### Game loop

`core/game.py` runs one level at a time. Each frame:

1. Poll events (movement keys, point-and-click pathfinding target, pause, cheat menu, quit).
2. Step `Monitor` forward (entity positions, collisions, super pac-gum frightened timer).
3. Check win / lose / time-up conditions.
4. If the player is dying, advance the death-animation timer before resetting the level.
5. Render via `PygameViewer.render_frame()`.

A `time_up` flag distinguishes a ghost death (preserve `elapsed`) from a clock-expired death (reset `elapsed` to 0). On level start and after each respawn, all pygame events are blocked for 2 seconds and the event queue is flushed, so buffered keypresses cannot leak across resets.

### Ghost AI

Each ghost extends an abstract `Ghost` class and overrides only `choose_target()`:

| Ghost | Behaviour |
|-------|-----------|
| **Blinky** | Direct chase — always targets Pac-Man's exact cell |
| **Pinky** | Ambush — targets 4 cells ahead of Pac-Man's facing direction |
| **Inky** | Flanking — reflects Blinky's position through 2 cells ahead of Pac-Man (falls back to direct chase if Blinky has been eaten) |
| **Clyde** | Shy — chases when more than 8 tiles away, retreats to his spawn corner when close |

In frightened mode all ghosts move pseudo-randomly and never make 180° turns unless trapped. Blinky enters "Elroy" mode (speed boost) at 75% pac-gums eaten and a second boost at 90%. Eaten ghosts respawn in their corner after a configurable delay.

### Cheat mode

Triggered by `C` during play if `cheat_mode` is enabled. The menu offers:

- **No collision** — Pac-Man can phase through ghosts without losing a life.
- **Pause ghosts** — Freezes all ghost AI in place.
- **Add life** — Grants one extra life (current count is shown next to the entry).
- **Next level** — Instantly wins the current level.

Active cheats are listed bottom-left of the HUD in green during play and persist across levels.

### Helper popups

`display/helper.py` provides a Minecraft achievement-style toast that slides in from the top-right after a 1-second delay. One popup fires per screen entry:
- *Lobby:* "Point and click to select"
- *Arcade menu:* "Point and click or arrows"
- *Config editor:* "use arrow to select"

### Audio

`core/sounds.py` wraps `pygame.mixer` with a lazy, fail-safe loader. It reserves channels for menu music and fan ambience, exposes one-shot SFX (`play`), and lets the screamer halt the jumpscare audio in sync with the visual fade-out. Arrow-key navigation in the config editor plays `movement_select`, cutting the previous channel if the player spams keys. The arcade death animation also plays `jumpscare.mp3` and a full-screen FNAF-style screamer, with the sound stopping when the visual fade ends.

### Configuration editor

`core/config.py` exposes a CRT-style editor reached by clicking the retro computer in the lobby. A power-on animation (`computer_on.mp3`) plays on entry, the player navigates parameters with arrow keys, edits them through modal dialogs (boolean toggle, integer stepper with min/max clamping and key-repeat, free-text editor), and ESC triggers the power-off animation (`computer_off.mp3`) before saving the updated JSON back to disk.

---

## General Software Architecture

```
pac-man.py            Entry point — argv check, parser, Redirect.main_menu()

core/
  parser.py           JSON-with-comments parsing, validation, clamping, defaults
  config.py           In-game CRT-style config editor
  redirect.py         Hub/lobby screen — polygon hit-testing, transition anims
  game.py             Per-level game loop (input, state stepping, win/lose)
  monitor.py          Authoritative game state (grid, entities, items)
  scores.py           Highscore load/validate/sort/save
  sounds.py           Lazy pygame.mixer wrapper (SFX, music, fan ambience)

entities/
  entity.py           Base class shared by player and ghosts
  player.py           PacMan — movement, lives, score, super state, death anim
  ghost.py            Abstract Ghost — shared movement, frightened, U-turn rules
  ghost_types.py      Blinky, Pinky, Inky, Clyde — only override choose_target()
  items.py            Pacgum, SuperPacgum

display/
  pygame_viewer.py    PygameViewer — composes the mixins, owns screen + flow
  renderer_mixin.py   Maze / item / sprite / wall drawing
  hud_mixin.py        In-game HUD (score, lives, level, timer, active cheats)
  screens_mixin.py    Fullscreen UI loops (arcade menu, highscores, instructions,
                      end / win / pause / cheat menus, jumpscare screamer)
  sprite_mixin.py     Sprite loading, scaling, animation frames
  helper.py           Achievement-style toast popup (top-right, slide-in)
  _maze_utils.py      Maze generator wrapper + cache

animation/            WebP frames for lobby idle + arcade/computer transitions
assets/
  Sound/              SFX and music (mp3 / wav)
  Sprites/            Pac-Man + ghosts sprite sheets
  Typo/               ByteBounce.ttf + texts.png
  Utils/              Logo, lobby background, screamer image
  Maze/               Maze tile assets

config/config.json    Default configuration file
scores/<n>/highscores.json   Per-difficulty highscore files
mazegenerator-00001-py3-none-any.whl   Assigned A-Maze-ing wheel

Makefile              install / run / debug / clean / lint / lint-strict / package
pyproject.toml        uv-managed dependencies
pac-man.spec          PyInstaller spec generated by `make package`
```

**Key design choices**

- `PygameViewer` is composed from four mixins (`RendererMixin`, `HudMixin`, `ScreensMixin`, `SpritesMixin`) to keep each concern in its own file while sharing a single `self.screen`.
- `Monitor` is the **single source of truth** for game state; neither the renderer nor the game loop mutates entities directly without going through it.
- `Ghost` is `abc.ABC`; each ghost subclass only implements `choose_target()`, inheriting all movement, collision, frightened, U-turn, and respawn logic.
- The maze generator package is treated as a black box — only the result grid is read; the package itself is never modified, only a single recursive helper is patched out at the call-site.
- All disk I/O (config, highscores) uses context managers and catches `OSError` / `JSONDecodeError` explicitly to guarantee no traceback ever reaches the user.

---

## Project Management

The project was managed jointly by **mlorenzo** and **avauclai** over four weeks (early May to early June 2026).


### Brief overview

| Period | Focus |                                                                                                                                                    
|--------|-------| 
| 06–08/05 | Architecture decisions, entity classes, ghost AI prototypes, parser | 
| 09–11/05 | Pygame viewer, ghost integration into the game loop, menu, scoring | 
| 12–14/05 | Sprite system, animations, level progression, cheat mode, 3D Blender renders | 
| 15–21/05 | Pause menu, fullscreen mode, in-game config editor, flake8/mypy compliance | 
| 22–27/05 | Lobby hub, point-and-click controls, jumpscare, packaging spec, parser polish | 
| 28/05–01/06 | Helper popups, full sound design, README + project-management docs, packaging | 

### Timeline

```
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
		- Telemetry Dashboard: Added a real-time debug overlay in the terminal to monitor ghost targets, positions, and active modes.
		- UI Development: Created a 90s Windows-style main menu in Pygame featuring beveled buttons and a teal aesthetic.
		- Transition Effects: Implemented a cinematic fade-to-black system to handle smooth loading between the menu and the game.
		- 3D Integration: Prepared the engine to display high-quality pre-rendered 3D scenes created in Blender.
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
	mlorenzo :
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
		- The Pacgums weren't spawning in the corners, probably because of the position of the ghosts, so I fixed it.
		- We have noticed that the walls without any squares of other surrounding walls were treated as empty squares. So to fix it, I filled these walls with a rectangle the width of the walls
14/05/2026 :
	avauclai :
		- Animation on the launch screen
		- Creation of the GodMod
		- Implementation of the level system.
		- We have become aware of the challenge related to the weight/quality ratio of animation images, which is imposed by the Git of 42.
		- I have finished the main piece without animation of the 3D render.
15/05/2026 :
	avauclai :
		- We understood that the most suitable format was WebP, compress to 100%. We are still thinking about how to integrate the image volume on the git in the most intelligent way possible.
		- Start of animations (BaseAnimation, TransitionToArcade) stored on a drive
		- removal of ASCII mode
	mlorenzo :
		- Added the current level to the game window
		- Edited the scores file storqge, to have a specialized files for each difficulty level
		- Made the win screen working by adding "level" to the config of monitor
		- Reorganization of the pygame_viewer in multiples files for better understanding
		- Added the augmentation of the size of the maze for the difficulty 3 and above (+3 for difficulty 3 and 4, and +6 for difficulty 5)
19/05/2026 :
	mlorenzo :
		- Pause menu implemented
21/05/2026 :
	mlorenzo :
		- Cheat menu fully implemented
		- Reorganisation to put game logic in game.py
		- All cheats implemented, and staying on throughout the levels
		- Added the reroll of the maze when half of the requiered time is used at level 5
		- Adapted the project to respect mypy and flake8
		- Small Re design of the pause and cheat window
		- Corrected some incoherences between the code and the subject, such as the cheat menu when cheatmod off, or points_per_ghosts partially ignored
22/05/2026 :
	mlorenzo :
		- Edited the windows to be full screen at all time
		- Did the config.py wich will contain the edit of the config throughout the computer of the Hub of the game
		- Edits to pass through flake8 and mypy without any issues
		- Added dynamiic size to text, so that it fill the screen entirely and not only the base text
		- Finished all the game, missing only the animations and the debugg, and some re-design
		- Perfected parsing with files verifs, and warning for unknown key(s)
		- Instructions were stackable during the freeze at the start of each level, corrected by clearing the events at the end of the time sleep in pygame_viewer.py
23/05/2026 :
	mlorenzo :
		- Design improvments
		- Added the READY at the start of levels/Reset
		- Added the typos for each caracters needed
		- Didn't find any bugs yet
24/05/2026 :
	mlorenzo :
		- Adapted the path for the animation to link up to all the files
		- changed the config.py starting and closing animation to match the screen already on
25/05/2026 :
	mlorenzo :
		- Created the rule for the binary package requiered
		- Cleaned the visuals
		- Changed the creation of a new window for each transition to a reuse of the original one
		- Changed the max/min values for config, and maze size because of the performances.
26/05/2026 :
	mlorenzo :
		- Raised the recursion limit cap up to 10000 for maze generation, to not crash out for large maze due to python recursion limit
		- core/parser.py rewritten:
			- Lines starting with `#` are parsed as comms before json parse the file entirely
			- Factored the per-key checks into `_is_int` and `_is_bool` helpers + a DEFAULTS dict
			- Missing keys now use the default value with a warning, instead of refusing to start
		- Added the docstrings
		- Removed god mode as it's the same than collision
		- Add a cheat to add one more life
27/05/2026 :
	mlorenzo :
		- Finished the implementation of the point and click to the game itself, for a more intuitive game experience
		- Lighten the code to be more readable and less heavy
		- Added the screamer of loss
		- Started adding the sounds
01/06/2026 :
	mlorenzo :
		- Added a helper in a achievment minecraft style
		- Finished the sound implementation
		- Adapted the make packages to adapt whatever the OS is
		- Finalized the README
		- Corrected some crash if file not found or not accessible
		- Removed the _Fast_MazeGenerator as a patch on the packages as been published
		- Changed the dimmension of the maze to test in the beggining of the programm, to avoid the warning message for the 42 size, wich is unusefull
		- Re adapted the code for the make lint
```

---

## Resources

- [Pac-Man Fandom Wiki](https://pacman.fandom.com/wiki/Pac-Man_Wiki) — original mechanics and lore
- [How Pac-Man Ghost AI Works](https://aighost.co.uk/how-pac-man-ghost-ai-works-the-classic-chase-algorithms/) — Blinky / Pinky / Inky / Clyde target rules
- [Play classic Pac-Man](https://pacman.live/play.html) — reference behaviour for tuning
- [Pygame documentation](https://www.pygame.org/docs/) — surface, mixer, event, font, transform
- [Advanced OpenGL in Python with Pygame](https://stackabuse.com/advanced-opengl-in-python-with-pygame-and-pyopengl/) — investigated for the transition animations

### AI usage

AI tooling (Claude Code) was used selectively, as a productivity multiplier on tasks where the team already knew the desired outcome:

- **Repetitive code generation:** type hints, docstrings, mixin boilerplate, scaffolding for the polygon hit-test math in the lobby.
- **README scaffolding:** initial structure of this file and tables, then audited section-by-section against the actual code.

The AI was **not** used to design the architecture, the ghost AI rules, the parser semantics, the highscore model, or the packaging strategy — those were decided by the team. Every AI-generated diff was read, edited, run, and tested before being committed; nothing went in that the team could not explain end-to-end.

