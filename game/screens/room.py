from game.screens.placeholder import PlaceholderScreen
from game.screens.screen import ScreenId


class RoomScreen(PlaceholderScreen):
    def __init__(self, size: tuple[int, int]) -> None:
        super().__init__(
            size,
            "Main room is not built yet",
            ScreenId.INTERACTION,
        )
