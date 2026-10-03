from game.tasks.base import TaskDefinition
from game.state import Location


TASK = TaskDefinition(
    location=Location.POND,
    title="The Pond",
    elf_path="Use the net to sort the waste and clean the pond.",
    fae_path="Use the net to pull the key out of the pond.",
)
