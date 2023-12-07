# @Copyright: CEA-LIST/DIASI/SIALV/LVA (2023)
# @Author: CEA-LIST/DIASI/SIALV/LVA <pixano@cea.fr>
# @License: CECILL-C
#
# This software is a collaborative computer program whose purpose is to
# generate and explore labeled data for computer vision applications.
# This software is governed by the CeCILL-C license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-C
# license as circulated by CEA, CNRS and INRIA at the following URL
#
# http://www.cecill.info

import click
import pkg_resources

from pixano.apps.serve import App

LOGO = """
                             ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒
                           ▒▓▒                                       ▓
              █▓          ▓▓                                         ▓
                        ▒▓▒   ▒▓▓▓▓▓ ▒▓   ▓▒▒▓▓▓▓▒     ▒▓▓▓▓▓▒       ▓
▓▓ ▓▓▓▓▓▓▒    ▓▒  ▒▓   ▓▒   ▒▓      ▓██   ██     ▓▒  ▒█▓     ▒█▓     ▓
███      ▓▓   █▒   ▓█      ▒█▒       ██   █▒     ▒█  ▓▒        █     ▓
██        █▒  █▒    ▒█▓     █▒       ██   █▒     ▒█  ▓▓        █     ▓
██        █▒  █▒    ▓█▓█     █▒     ▓██   █▒     ▒█   ██     ▓█▒     ▓
██▓▒    ▒▓▒   █▒   ▓▒  ▒█▓    ▒▓▓▓▓▓ ▒▓   ▓      ▒▓    ▒▓▓▓▓▓▒       ▓
██  ▒▓▓▒▒     ▒   ▒      ▒▓▒                                         ▓
██                         █▓                                        ▓
"""
ASSETS_PATH = pkg_resources.resource_filename("pixano", "apps/annotator/dist/assets")
TEMPLATE_PATH = pkg_resources.resource_filename("pixano", "apps/annotator/dist")


class Annotator(App):
    """Pixano Annotator App

    Attributes:
        config (uvicorn.Config): App config
        server (uvicorn.Server): App server
        assets_path (str): Path to App assets directory
        template_path (str): Path to App template directory
    """

    def __init__(
        self,
        library_dir: str,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        """Initialize and run Pixano Annotator app

        Args:
            library_dir (str): Dataset library directory
            host (str, optional): App host. Defaults to "127.0.0.1".
            port (int, optional): App port. Defaults to 0.
        """

        self.assets_path = ASSETS_PATH
        self.template_path = TEMPLATE_PATH

        super().__init__(library_dir, host, port)


@click.command(context_settings={"auto_envvar_prefix": "UVICORN"})
@click.argument(
    "library_dir",
    type=str,
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Bind socket to this host.",
    show_default=True,
)
@click.option(
    "--port",
    type=int,
    default=0,
    help="Bind socket to this port.",
    show_default=True,
)
def main(library_dir: str, host: str, port: int):
    """Launch Pixano Annotator

    LIBRARY_DIR: Dataset library directory
    """
    Annotator(library_dir, host, port)
