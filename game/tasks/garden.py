from game.tasks.base import TaskDefinition
from game.state import Location


TASK = TaskDefinition(
    location=Location.GARDEN,
    title="The Garden",
    elf_path="Complete the maze and give the gathered food to the Elf.",
    fae_path="Complete the maze and give the gathered food to the Fae.",
)
