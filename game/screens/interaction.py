from game.screens.placeholder import PlaceholderScreen
from game.screens.screen import ScreenId


class InteractionScreen(PlaceholderScreen):
    def __init__(self, size: tuple[int, int]) -> None:
        super().__init__(
            size,
            "Interactions and tasks are not built yet",
            ScreenId.EPILOGUE,
        )
