"""
Test script to display animation frames using Pygame.
"""
import os
import sys

import pygame


def main():
    pygame.init()

    # Setup window
    width, height = 1980, 1600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Animation Test")

    clock = pygame.time.Clock()

    # Load images
    base_path = os.path.join("assets",
                             "GameFootage",
                             "Animation Pacman",
                             "BaseAnimation")
    transition_path = os.path.join("assets",
                                   "GameFootage",
                                   "Animation Pacman",
                                   "TransitionToDesktop")

    base_images = []
    transition_images = []

    for i in range(1, 11):
        filename = f"{i:04d}.png"
        path = os.path.join(base_path, filename)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            base_images.append(img)
        else:
            print(f"Warning: {path} not found")

    for i in range(1, 61):
        filename = f"{i:04d}.png"
        path = os.path.join(transition_path, filename)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            transition_images.append(img)
        else:
            print(f"Warning: {path} not found")

    if not base_images and not transition_images:
        print("No images found. Exiting.")
        pygame.quit()
        sys.exit()

    frame_index = 0
    fps = 30  # adjust speed here
    last_update = pygame.time.get_ticks()
    frame_duration = 1000 // fps

    running = True
    in_transition = False

    # Placeholder hitbox (replace with your object's hitbox later)
    # A 200x100 rectangle positioned at the top-left
    dummy_hitbox = pygame.Rect(50, 50, 200, 100)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if dummy_hitbox.collidepoint(event.pos) and not in_transition:
                        in_transition = True
                        frame_index = 0

        # Update frame
        now = pygame.time.get_ticks()
        if now - last_update > frame_duration:
            last_update = now

            if not in_transition:
                # Loop infinitely through the base animation
                frame_index = (frame_index + 1) % len(base_images)
            else:
                # Advance to the last frame for the transition
                if frame_index < len(transition_images) - 1:
                    frame_index += 1

        # Draw
        screen.fill((0, 0, 0))  # black background

        if not in_transition:
            current_img = base_images[frame_index]
        else:
            current_img = transition_images[frame_index]

        # Center image
        rect = current_img.get_rect(center=(width // 2, height // 2))
        screen.blit(current_img, rect)

        # Display the hitbox for testing (remove later)
        if not in_transition:
            pygame.draw.rect(screen, (255, 0, 0), dummy_hitbox, 2)
            font = pygame.font.SysFont(None, 36)
            text = font.render("Click here", True, (255, 0, 0))
            screen.blit(text, (dummy_hitbox.x + 10, dummy_hitbox.y + 35))

        pygame.display.flip()

        # Cap framerate
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
