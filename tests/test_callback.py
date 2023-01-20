#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-01-19
# @Filename: test_callback.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import unittest.mock

import click
from click.testing import CliRunner

from unclick.core import build_command_string


@click.command()
@click.argument("ARG1", type=str)
@click.argument("ARG2", type=int, required=False)
@click.option("--flag1", "-f", is_flag=True)
def my_command1(*args, **kwrgs):
    return


def _command_invoke(command: click.Command, string: str):
    """Checks that command is called and returns a mock of the callback."""

    with unittest.mock.patch.object(command, "callback") as mock_callback:
        runner = CliRunner()

        result = runner.invoke(command, string.split()[1:])
        assert result.exit_code == 0

        mock_callback.assert_called()

    return mock_callback


def test_callback():
    command_string = build_command_string(my_command1, "hi", 2, flag1=True)

    mock_callback = _command_invoke(my_command1, command_string)
    mock_callback.assert_called_once_with(arg1="hi", arg2=2, flag1=True)


def test_callback2():
    command_string = build_command_string(my_command1, "hi")

    mock_callback = _command_invoke(my_command1, command_string)
    mock_callback.assert_called_once_with(arg1="hi", arg2=None, flag1=False)
