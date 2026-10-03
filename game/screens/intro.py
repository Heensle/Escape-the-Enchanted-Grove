from game.screens.placeholder import PlaceholderScreen
from game.screens.screen import ScreenId


class IntroScreen(PlaceholderScreen):
    def __init__(self, size: tuple[int, int]) -> None:
        super().__init__(
            size,
            "Intro scene is not built yet",
            ScreenId.ROOM,
        )
