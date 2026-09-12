"""USER-RUN entry point: register the local repair step, then use OpenLane CLI."""
import antenna_closure  # noqa: F401; registration only
from openlane.__main__ import cli

if __name__ == '__main__':
    cli()
