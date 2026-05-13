import pygame
import sys


def transition_to_3d(screen: pygame.Surface, next_image_path: str) -> None:
    """
    1. Fade the menu to black.
    2. Load the Blender image.
    3. Fade the image in progressively.
    """
    width, height = screen.get_size()
    fade_surface = pygame.Surface((width, height))
    fade_surface.fill((0, 0, 0))

    # --- PHASE 1: FADE OUT (menu disappears) ---
    for alpha in range(0, 255, 8):  # Fade speed
        fade_surface.set_alpha(alpha)
        # Don't fill the screen; draw black ON TOP of the existing menu
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)

    # --- PHASE 2: LOADING ---
    # The screen is black — ideal time to load the image without visual lag
    try:
        raw_image = pygame.image.load(next_image_path).convert()
        # Resize the image to the current window size
        new_scene = pygame.transform.scale(raw_image, (width, height))
    except Exception as e:
        print(f"Loading error: {e}")
        return

    # --- PHASE 3: FADE IN (Blender image appears) ---
    for alpha in range(255, -1, -8):
        screen.fill((0, 0, 0))  # Clean black background
        screen.blit(new_scene, (0, 0))  # Draw the 3D image

        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))  # Draw the fading black overlay
        pygame.display.flip()
        pygame.time.delay(20)


def draw_retro_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    is_hovered: bool,
) -> None:
    """Draw a button with a 90s-style 3D relief effect."""
    # Typical colours
    GRAY = (192, 192, 192)
    WHITE = (255, 255, 255)
    DARK_GRAY = (128, 128, 128)
    BLACK = (0, 0, 0)

    # Button background
    pygame.draw.rect(screen, GRAY, rect)

    # Relief effect (Bevelling)
    if not is_hovered:
        # White borders (top and left)
        pygame.draw.line(screen, WHITE, (rect.x, rect.y),
                         (rect.x + rect.width, rect.y), 2)
        pygame.draw.line(screen, WHITE, (rect.x, rect.y),
                         (rect.x, rect.y + rect.height), 2)
        # Dark grey borders (bottom and right)
        pygame.draw.line(screen, DARK_GRAY, (rect.x + rect.width, rect.y),
                         (rect.x + rect.width, rect.y + rect.height), 2)
        pygame.draw.line(screen, DARK_GRAY, (rect.x, rect.y + rect.height),
                         (rect.x + rect.width, rect.y + rect.height), 2)
    else:
        # Inverted relief on hover or click
        pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, BLACK, rect, 1)

    # Text rendering
    text_color = BLACK
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def main() -> None:
    pygame.init()

    # Window configuration (resizable)
    screen_info = pygame.display.Info()
    sw, sh = int(screen_info.current_w * 0.6), int(screen_info.current_h * 0.6)
    screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    pygame.display.set_caption("Retro Menu 90s")

    # Font (Monospace gives a terminal/old PC look)
    # A font like 'MS Sans Serif' would look even better
    font = pygame.font.SysFont("Courier", 32, bold=True)

    clock = pygame.time.Clock()

    options = ["Start Game", "Settings", "Leave"]

    running = True
    while running:
        current_sw, current_sh = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h),
                                                 pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Simplified click logic
                for i in range(len(options)):
                    button_rect = pygame.Rect(current_sw//2 - 150,
                                              current_sh//3 + i*80, 300,
                                              60)
                    if button_rect.collidepoint(mouse_pos):
                        print(f"Action: {options[i]}")
                        if options[i] == "Start Game":
                            # Launch the transition to Blender rendering
                            transition_to_3d(screen,
                                             "assets/votre_image_blender.png")
                        elif options[i] == "Leave":
                            running = False

        # Background colour "Windows Blue" or "Desktop Grey"
        screen.fill((0, 128, 128))  # Typical Win95 teal

        # Draw the menu title
        title_surf = font.render("MAIN MENU", True, (255, 255, 255))
        screen.blit(title_surf, (current_sw//2 - title_surf.get_width()//2,
                                 50))

        # Draw the buttons
        for i, text in enumerate(options):
            button_w, button_h = 300, 60
            button_x = current_sw // 2 - button_w // 2
            button_y = current_sh // 3 + i * 80

            rect = pygame.Rect(button_x, button_y, button_w, button_h)
            is_hovered = rect.collidepoint(mouse_pos)

            draw_retro_button(screen, rect, text, font, is_hovered)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
