"""
Animation script for 90 frames in TransitionToDesktop folder.
"""
import os
import sys
import pygame

def main():
    pygame.init()

    # Configuration de la fenêtre
    # Garde tes dimensions initiales ou adapte selon la sortie Blender
    width, height = 1920, 1080 
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Transition Test - 90 Frames")

    clock = pygame.time.Clock()

    # Configuration du dossier
    folder_path = "TransitionToArcade"
    images = []

    # Chargement dynamique des 90 frames
    print(f"Loading frames from {folder_path}...")
    
    # On boucle de 0 à 90
    for i in range(0, 90):
        # Formatage du nom : 0001.webp, 0002.webp, etc.
        filename = f"{i:04d}.webp"
        path = os.path.join(folder_path, filename)
        
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                images.append(img)
            except pygame.error as e:
                print(f"Could not load image {path}: {e}")
        else:
            # Optionnel : si tes frames commencent à 0000.webp, ajuste le range(0, 90)
            print(f"Warning: {path} not found")

    if not images:
        print(f"Error: No images found in '{folder_path}'. Check the folder name and extension.")
        pygame.quit()
        sys.exit()

    print(f"Successfully loaded {len(images)} frames.")

    frame_index = 0
    # 30 FPS est le standard pour une animation fluide sortant de Blender
    fps_animation = 60  
    last_update = pygame.time.get_ticks()
    frame_duration = 1000 // fps_animation

    running = True

    while running:
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Quitter aussi avec la touche Echap
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Mise à jour de l'index (Boucle)
        now = pygame.time.get_ticks()
        if now - last_update > frame_duration:
            last_update = now
            frame_index = (frame_index + 1) % len(images)

        # Dessin
        screen.fill((20, 20, 20)) # Fond sombre

        current_img = images[frame_index]
        
        # Centrage automatique de la frame
        rect = current_img.get_rect(center=(width // 2, height // 2))
        screen.blit(current_img, rect)

        pygame.display.flip()

        # On garde le tick à 60 pour la réactivité du clavier/souris
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()