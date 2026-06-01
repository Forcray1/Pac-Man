from __future__ import annotations

import os

import pygame

from display._maze_utils import _ROOT

_SOUND_DIR = os.path.join(_ROOT, "assets", "Sound")


class SoundManager:
    """
    Lazy, fail-safe wrapper around pygame.mixer for short SFX.
    """

    _instance: "SoundManager | None" = None
    _MUSIC_CHANNEL_ID = 0
    _FAN_CHANNEL_ID = 1
    _SOUND_EXTS = (".wav", ".mp3", ".ogg")

    def __init__(self) -> None:
        """
        Bring up pygame.mixer and reserve channels 0 (music) and 1 (fan).
        """
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._loops: dict[str, pygame.mixer.Channel] = {}
        self._music_state: tuple[str, ...] | None = None
        self._menu_music_path: str | None = None
        self._sfx_master: float = 1.0
        self._enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            try:
                pygame.mixer.set_num_channels(16)
                pygame.mixer.set_reserved(2)
            except pygame.error:
                pass
            self._enabled = True
        except pygame.error:
            self._enabled = False

    def _load(self, name: str) -> "pygame.mixer.Sound | None":
        """
        Return the cached Sound for name, loading it on first use.
        """
        if name in self._sounds:
            return self._sounds[name]
        if not self._enabled:
            self._sounds[name] = None
            return None
        path: str | None = None
        for ext in self._SOUND_EXTS:
            candidate = os.path.join(_SOUND_DIR, f"{name}{ext}")
            if os.path.exists(candidate):
                path = candidate
                break
        if path is None:
            self._sounds[name] = None
            return None
        try:
            snd = pygame.mixer.Sound(path)
        except pygame.error:
            self._sounds[name] = None
            return None
        self._sounds[name] = snd
        return snd

    def preload_all(self) -> None:
        """
        Eagerly load every audio file in assets/Sound/ into the cache.
        """
        if not self._enabled or not os.path.isdir(_SOUND_DIR):
            return
        for entry in os.listdir(_SOUND_DIR):
            lower = entry.lower()
            # main_menu is streamed via pygame.mixer.music, not Sound.
            if lower.startswith("main_menu."):
                continue
            for ext in self._SOUND_EXTS:
                if lower.endswith(ext):
                    self._load(entry[:-len(ext)])
                    break

    def set_sfx_master_volume(self, factor: float) -> None:
        """
        Scale all in-arcade SFX/music/loop volumes by factor.
        """
        self._sfx_master = max(0.0, min(1.0, factor))

    def _scaled(self, volume: float) -> float:
        """
        Apply the arcade SFX master multiplier and clamp to [0, 1].
        """
        return max(0.0, min(1.0, volume * self._sfx_master))

    def play(
        self, name: str, volume: float = 1.0,
    ) -> "pygame.mixer.Channel | None":
        """
        Play the sound name once (no looping). Returns the channel so the
        caller can stop or query it; None if the sound is missing.
        """
        snd = self._load(name)
        if snd is None:
            return None
        snd.set_volume(self._scaled(volume))
        return snd.play()

    def loop_start(self, name: str, volume: float = 1.0) -> None:
        """
        Start an infinite loop of name. Idempotent.
        """
        existing = self._loops.get(name)
        if existing is not None and existing.get_busy():
            existing.set_volume(self._scaled(volume))
            return
        snd = self._load(name)
        if snd is None:
            return
        snd.set_volume(self._scaled(volume))
        channel = snd.play(loops=-1)
        if channel is not None:
            self._loops[name] = channel

    def loop_stop(self, name: str) -> None:
        """
        Stop a loop started by loop_start. Idempotent.
        """
        channel = self._loops.pop(name, None)
        if channel is not None:
            channel.stop()

    def get_length(self, name: str) -> float:
        """
        Return the duration of sound name in seconds, or 0.0 if missing.
        """
        snd = self._load(name)
        if snd is None:
            return 0.0
        return snd.get_length()

    def _music_channel(self) -> "pygame.mixer.Channel":
        """
        Return the reserved channel used for the music bed.
        """
        return pygame.mixer.Channel(self._MUSIC_CHANNEL_ID)

    def music_play_loop(self, name: str, volume: float = 1.0) -> None:
        """
        Loop name on the reserved music channel. Idempotent.
        """
        if not self._enabled:
            return
        snd = self._load(name)
        if snd is None:
            return
        ch = self._music_channel()
        if (
            self._music_state == ("loop", name)
            and ch.get_busy()
            and ch.get_sound() is snd
        ):
            snd.set_volume(self._scaled(volume))
            return
        snd.set_volume(self._scaled(volume))
        ch.play(snd, loops=-1)
        self._music_state = ("loop", name)

    def music_play_chain(
        self, intro_name: str, loop_name: str, volume: float = 1.0,
    ) -> None:
        """
        Play intro_name once, then loop loop_name forever. Idempotent.
        """
        if not self._enabled:
            return
        ch = self._music_channel()
        intro = self._load(intro_name)
        loop = self._load(loop_name)
        state = self._music_state

        if (
            state == ("chain_intro", intro_name, loop_name)
            and intro is not None
        ):
            if ch.get_busy() and ch.get_sound() is intro:
                intro.set_volume(self._scaled(volume))
                return
            if loop is None:
                self._music_state = None
                return
            loop.set_volume(self._scaled(volume))
            ch.play(loop, loops=-1)
            self._music_state = ("chain_loop", intro_name, loop_name)
            return

        if state == ("chain_loop", intro_name, loop_name) and loop is not None:
            if ch.get_busy() and ch.get_sound() is loop:
                loop.set_volume(self._scaled(volume))
                return
            loop.set_volume(self._scaled(volume))
            ch.play(loop, loops=-1)
            return

        if intro is None:
            if loop is None:
                return
            loop.set_volume(self._scaled(volume))
            ch.play(loop, loops=-1)
            self._music_state = ("chain_loop", intro_name, loop_name)
            return
        intro.set_volume(self._scaled(volume))
        ch.play(intro)
        self._music_state = ("chain_intro", intro_name, loop_name)

    def music_stop(self) -> None:
        """
        Stop whatever is on the music channel. Idempotent.
        """
        if not self._enabled:
            return
        self._music_channel().stop()
        self._music_state = None

    def _fan_channel(self) -> "pygame.mixer.Channel":
        """
        Return the reserved channel used for fan ambience.
        """
        return pygame.mixer.Channel(self._FAN_CHANNEL_ID)

    def fan_play(self, name: str, volume: float = 1.0) -> None:
        """
        Drive the fan ambience loop on its reserved channel.
        """
        if not self._enabled:
            return
        snd = self._load(name)
        if snd is None:
            return
        ch = self._fan_channel()
        volume = max(0.0, min(1.0, volume))
        if ch.get_busy() and ch.get_sound() is snd:
            ch.set_volume(volume)
            return
        snd.set_volume(volume)
        ch.play(snd, loops=-1)
        ch.set_volume(volume)

    def fan_set_volume(self, volume: float) -> None:
        """
        Set the fan channel volume in-place without restarting.
        """
        if not self._enabled:
            return
        self._fan_channel().set_volume(max(0.0, min(1.0, volume)))

    def fan_stop(self) -> None:
        """
        Stop the fan loop. Idempotent.
        """
        if not self._enabled:
            return
        self._fan_channel().stop()

    def menu_music_play(self, name: str, volume: float = 1.0) -> None:
        """
        Loop background menu music via pygame.mixer.music. Idempotent.
        """
        if not self._enabled:
            return
        path: str | None = None
        for ext in (".mp3", ".ogg", ".wav"):
            candidate = os.path.join(_SOUND_DIR, f"{name}{ext}")
            if os.path.exists(candidate):
                path = candidate
                break
        if path is None:
            return
        volume = max(0.0, min(1.0, volume))
        if (
            self._menu_music_path == path
            and pygame.mixer.music.get_busy()
        ):
            pygame.mixer.music.set_volume(volume)
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1)
        except pygame.error:
            return
        self._menu_music_path = path

    def menu_music_set_volume(self, volume: float) -> None:
        """
        Set the menu music volume in-place without restarting.
        """
        if not self._enabled:
            return
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def menu_music_stop(self) -> None:
        """
        Stop the menu music stream. Idempotent.
        """
        if not self._enabled:
            return
        pygame.mixer.music.stop()
        self._menu_music_path = None

    def stop_all_loops(self) -> None:
        """
        Stop every active Sound channel except the fan ambience.
        """
        if not self._enabled:
            return
        for i in range(pygame.mixer.get_num_channels()):
            if i == self._FAN_CHANNEL_ID:
                continue
            pygame.mixer.Channel(i).stop()
        self._loops.clear()
        self._music_state = None


def get_sounds() -> SoundManager:
    """
    Return the process-wide SoundManager singleton.
    """
    if SoundManager._instance is None:
        SoundManager._instance = SoundManager()
    return SoundManager._instance
