# Skeleton of a CLI

import click

from varlib.parse import build_graph


@click.command('varlib')
@click.argument('vardef_yml', type=str, metavar='N')
def cli(vardef_yml):
    """build and print dependency graph"""
    build_graph(vardef_yml, verbose=True)
