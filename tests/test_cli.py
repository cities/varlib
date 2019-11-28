from click.testing import CliRunner

from varlib.scripts.cli import cli


def test_cli_build_graph():
    runner = CliRunner()
    result = runner.invoke(cli, "example/variables.yml")
    assert result.exit_code == 0
    #assert result.output == "False\nFalse\nFalse\n"
