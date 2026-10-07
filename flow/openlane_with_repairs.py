"""USER-RUN entry point: register the local repair step, then use OpenLane CLI."""
import antenna_closure
import electrical_eco_steps  # noqa: F401; registration only
import c40_monolithic_steps  # noqa: F401; RUN305 registration only
from openlane.__main__ import cli

if __name__ == '__main__':
    cli()
