from game.tasks.base import TaskDefinition
from game.state import Location


TASK = TaskDefinition(
    location=Location.POND,
    title="The Pond",
    elf_path="Sort the waste and clean the pond.",
    fae_path="Pull the key on the grate",
)
