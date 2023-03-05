#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-03-04
# @Filename: test_signature.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


import inspect

import click

from unclick import create_function, create_signature


@click.command(name="test-command")
@click.argument("ARG1", type=str)
@click.argument("ARG2", type=int, required=False)
@click.option("--flag1", "-f", is_flag=True)
@click.option("--option2", "-o", type=float, default=3.0)
@click.option("--shout/--no-shout")
@click.option("--shout2/--no-shout2", default=False)
@click.option("--shout3/--no-shout3", " /-S", default=True)
def command(*args, **kwrgs):
    return


def test_create_signature():
    """Create signature from a command."""

    sign = create_signature(command)
    assert isinstance(sign, inspect.Signature)
    assert len(sign.parameters) == 7


def test_create_function(mocker):
    """Create funcion from a command."""

    mock_func = mocker.MagicMock()

    func = create_function(command, mock_func, "my_generated_function")
    func("test", flag1=True)

    mock_func.assert_called_with(
        "test",
        arg2=None,
        flag1=True,
        option2=3.0,
        shout=False,
        shout2=False,
        shout3=True,
    )
