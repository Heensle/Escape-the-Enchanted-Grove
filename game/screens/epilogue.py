from game.screens.placeholder import PlaceholderScreen
from game.screens.screen import ScreenId


class EpilogueScreen(PlaceholderScreen):
    def __init__(self, size: tuple[int, int]) -> None:
        super().__init__(
            size,
            "The four days in the Enchanted Grove are complete",
            ScreenId.TITLE,
        )
