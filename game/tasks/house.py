from game.tasks.base import TaskDefinition
from game.state import Location


TASK = TaskDefinition(
    location=Location.HOUSE,
    title="The House",
    elf_path="Complete a jigsaw to repair the roof.",
    fae_path="Use the hammer task to break the gate lock.",
)
