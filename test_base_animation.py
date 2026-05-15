"""
Test script to display animation frames using Pygame.
"""
import os
import sys
import pygame

def main():
    pygame.init()

    # Configuration de la fenêtre
    width, height = 1920, 1080 # Ajusté pour un standard HD, modifie selon tes besoins
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Animation Test - Loop 6 Frames")

    clock = pygame.time.Clock()

    # Chargement des images
    base_path = "BaseAnimation"
    base_images = []

    # On charge les 6 frames au format .webp
    for i in range(1, 7):
        # Utilisation de f-string pour correspondre à tes noms de fichiers (ex: 0001.webp)
        filename = f"{i:04d}.webp"
        path = os.path.join(base_path, filename)
        
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            base_images.append(img)
        else:
            print(f"Warning: {path} not found")

    if not base_images:
        print("No images found in 'BaseAnimation/'. Check paths and extension. Exiting.")
        pygame.quit()
        sys.exit()

    frame_index = 0
    fps_animation = 60  # Vitesse de l'animation (images par seconde)
    last_update = pygame.time.get_ticks()
    frame_duration = 1000 // fps_animation

    running = True

    while running:
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Mise à jour de l'index de la frame (Logique de boucle)
        now = pygame.time.get_ticks()
        if now - last_update > frame_duration:
            last_update = now
            # Boucle infinie sur les 6 images
            frame_index = (frame_index + 1) % len(base_images)

        # Dessin
        screen.fill((30, 30, 30))  # Fond gris foncé pour mieux voir les contours

        current_img = base_images[frame_index]
        
        # Centrage de l'image
        rect = current_img.get_rect(center=(width // 2, height // 2))
        screen.blit(current_img, rect)

        pygame.display.flip()

        # Cap du moteur à 60 FPS (pour la fluidité des événements)
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()