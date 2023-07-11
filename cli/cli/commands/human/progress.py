import typing as t

import scaleway.rdb.v1 as rdb
from rich.progress import BarColumn, Progress, ProgressColumn
from rich.style import Style

# Colors from the Ultraviolet design system
# Reference:
# https://brand.ultraviolet.scaleway.com/6dd9b5c45/p/85075b-colors--gradients/b/337612
ULTRAVIOLET_PRIMARY_PURPLE = "#4F0599"
ULTRAVIOLET_SECONDARY_PURPLE = "#8430D9"
ULTRAVIOLET_GREEN = "#45D29F"

# This parameter is used to make the progress bar more stiff
# Lower values make the bar more smooth
STIFFNESS = 0.2

ULTRAVIOLET_GREEN_STYLE = Style(color=ULTRAVIOLET_GREEN)


def get_ultraviolet_styled_progress_columns() -> t.Tuple[ProgressColumn, ...]:
    # We remove the estimated time because it doesn't work well with
    # not so granular progress
    (description, progress_bar, percentage, *_) = Progress.get_default_columns()
    progress_bar = t.cast(BarColumn, progress_bar)
    progress_bar.style = Style(color=ULTRAVIOLET_PRIMARY_PURPLE)
    progress_bar.pulse_style = Style(color=ULTRAVIOLET_SECONDARY_PURPLE)
    progress_bar.complete_style = Style(color=ULTRAVIOLET_SECONDARY_PURPLE)
    return (description, progress_bar, percentage)


def mix(a: float, b: float, amount: float) -> float:
    """Mix two values together with a given amount."""
    return (1 - amount) * a + amount * b


def database_deployment_progress_cb(
    progress: Progress,
) -> t.Callable[[rdb.Instance], None]:
    """Create a callback that handles the database creation progress."""

    db_task = progress.add_task("Deploying database", total=100, start=False)

    def wait_for_database_on_tick(instance: rdb.Instance) -> None:
        progress.start_task(db_task)
        if instance.status == rdb.InstanceStatus.READY:
            progress.update(db_task, completed=100, refresh=True)
            progress.stop()
        elif instance.status == rdb.InstanceStatus.PROVISIONING:
            # First part of creating is provisioning
            task = progress.tasks[db_task]
            task.description = "Provisioning database (1/2)"
            completed = mix(task.completed, 50, STIFFNESS)
            progress.update(db_task, completed=completed)
        elif instance.status == rdb.InstanceStatus.INITIALIZING:
            # Second part of creating is initializing
            task = progress.tasks[db_task]
            task.description = "Initializing database (2/2)"
            completed = mix(task.completed, 100, STIFFNESS * 2)
            progress.update(db_task, completed=completed)
        elif instance.status == rdb.InstanceStatus.ERROR:
            progress.stop()

    return wait_for_database_on_tick
