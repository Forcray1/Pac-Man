## Config File

- "level": Numbers of levels
- "width": Width of the first maze
- "height": Height of the first maze
- "difficulty": Difficulty from 1 to 5:
	- 1: No buffs on the ghosts, and the maze size stay still throughout the game
	- 2: Ghosts are a bit faster than level 1
	- 3: Maze is increasing in size at each level
	- 4: Ghosts are faster than level 3
	- 5: Ghosts are at theire fastest, and the maze is randomized each 30 seconds
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


# Edits since last commit:


# Edit a faire : 
Crash si tu mets "None" en pseudo pour le highscore.
Je comprend pas le bug. J'avais lance normalement, tout marchait, puis j'ai mit None en pseudo pour test, et la il me met le message en dessous. Il cherchait scores/3/highscores.json mais avait il semblait chercer scores/1/highscores.json, c'est comme si le None avait change le chemin. Donc la j'ai remis highscores 3 en destination. Trop bizarre.

UPDATE : J'ai compris l'erreur, la difficulty dans le fichier config fait changer le numero de dossier pour les highscores. Peut etre est-ce une confusion avec les levels et pas la difficulte. 

Traceback (most recent call last):
  File "/home/avauclai/Desktop/Pac-Man/pac-man.py", line 32, in <module>
    main()
    ~~~~^^
  File "/home/avauclai/Desktop/Pac-Man/pac-man.py", line 28, in main
    viewer.display()
    ~~~~~~~~~~~~~~^^
  File "/home/avauclai/Desktop/Pac-Man/display/pygame_viewer.py", line 713, in display
    self._run_end_screen(
    ~~~~~~~~~~~~~~~~~~~~^
        result, self.monitor.player.score
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/avauclai/Desktop/Pac-Man/display/pygame_viewer.py", line 874, in _run_end_screen
    self.score_manager.add(
    ~~~~~~~~~~~~~~~~~~~~~~^
        name or "Anonymous", final_score
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/avauclai/Desktop/Pac-Man/core/scores.py", line 82, in add
    self.save()
    ~~~~~~~~~^^
  File "/home/avauclai/Desktop/Pac-Man/core/scores.py", line 41, in save
    with open(self.filename, "w", encoding="utf-8") as f:
         ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'scores/3/highscores.json'


Il faut mettre en place les difficultes. Elles dependent du fichier de config. La signification des niveaux de difficultes se trouvent dans le readme. Le premier niveau ne doit jamais etre soumis a la difficultes.