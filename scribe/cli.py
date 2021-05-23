import os
import shutil
from pathlib import Path
from typing import Optional

import typer

from .__version__ import __version__

app = typer.Typer()
config = typer.Typer()


# ------------------------------------------------------------------------------------ #
#                                   General Commands                                   #
#                                                                                      #
#                                        version                                       #
#                                   version_callback                                   #
#                                     app_callback                                     #
# ------------------------------------------------------------------------------------ #
@app.command()
def version():
    typer.echo(__version__)


def version_callback(version: bool):
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def app_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    """
    Crypto-currencies market data recorder.
    """


# ------------------------------------------------------------------------------------ #
#                                     Config Group                                     #
#                                                                                      #
#                                    config_callback                                   #
#                                       generate                                       #
#                                         path                                         #
# ------------------------------------------------------------------------------------ #
@config.callback()
def config_callback():
    """
    Generate or show the configuration file.
    """


@config.command()
def generate():
    "Generate the default configuration file."
    source = Path(Path(__file__).parent, "scribe.yaml").resolve()
    destination = _configuration_path()
    try:
        os.mkdir(destination.parent)
    except FileExistsError:
        pass
    shutil.copy(source, destination)
    typer.echo(f"Generate default configuration: {destination}")


@config.command()
def path():
    "Show the path to the configuration file."
    typer.echo(_configuration_path())


def _configuration_path():
    """
    Path to the configuration file.
    """
    return Path(Path.home(), ".scribe/scribe.yaml").resolve()


# ------------------------------------------------------------------------------------ #
#                                     Main Command                                     #
# ------------------------------------------------------------------------------------ #
@app.command()
def start():
    "Start publishing prices."
    typer.echo("Start")


app.add_typer(config, name="config")
