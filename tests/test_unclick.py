#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-01-19
# @Filename: test_unclick.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import click
import pytest

from unclick import build_command_string, command_to_json


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


@click.command()
@click.option("--required", type=int, required=True)
def command_required(required: int):
    return


@click.command()
@click.argument("ARG", type=int, nargs=2)
def command_nargs2(arg: tuple[int, int]):
    return


@click.command()
@click.option("--tuple-option", type=click.Tuple([str, int]))
def command_tuple(tuple_option: tuple[str, int]):
    return


@click.command()
@click.option(
    "--bias",
    "flavour",
    flag_value="bias",
    default=True,
    show_default=True,
    help="Take a bias.",
)
@click.option(
    "--dark",
    "flavour",
    flag_value="dark",
    default=False,
    help="Take a dark.",
)
@click.option(
    "--flat",
    "flavour",
    flag_value="flat",
    default=False,
    help="Take a flat.",
)
def command_flag_value(flavour: str = "bias"):
    return


def test_build_command():
    json = command_to_json(command)
    assert isinstance(json, str)

    command_string = build_command_string(json, "hi", 1)
    assert command_string == 'test-command "hi" 1'

    command_string = build_command_string(json, "hi")
    assert command_string == 'test-command "hi"'

    command_string = build_command_string(command, arg1="hi", arg2=4)
    assert command_string == 'test-command "hi" 4'

    command_string = build_command_string(command, arg1="hi", option2=5)
    assert command_string == 'test-command --option2 5 "hi"'

    command_string = build_command_string(command, arg1="hi", option2=3.0)
    assert command_string == 'test-command "hi"'


@pytest.mark.parametrize(
    "kwargs,command_string",
    [
        ({"flag1": False}, 'test-command "hi"'),
        ({"flag1": True}, 'test-command --flag1 "hi"'),
        ({"shout": True}, 'test-command --shout "hi"'),
        ({"shout": False}, 'test-command "hi"'),
        ({"shout2": True}, 'test-command --shout2 "hi"'),
        ({"shout2": False}, 'test-command "hi"'),
        ({"shout3": True}, 'test-command "hi"'),
        ({"shout3": False}, 'test-command --no-shout3 "hi"'),
        ({"flag1": None, "shout": None, "shout2": None}, 'test-command "hi"'),
    ],
)
def test_boolean_flags(kwargs: dict, command_string: str):
    assert command_string == build_command_string(command, "hi", **kwargs)


def test_mismatched_type():
    with pytest.raises(TypeError) as err:
        build_command_string(command, "hi", option2="bye")

    err_msg = "Value 'bye' does not match type 'float' for parameter 'option2'."
    assert str(err.value) == err_msg


def test_none_as_arg():
    with pytest.raises(ValueError) as err:
        build_command_string(command, None)

    assert str(err.value) == "'None' cannot be used as value for argument 'arg1'."


def test_too_many_args():
    with pytest.raises(ValueError) as err:
        build_command_string(command, "hi", 5, "bye")

    assert str(err.value) == "More arguments provided than expected."


def test_missing_args():
    with pytest.raises(ValueError) as err:
        build_command_string(command)

    assert str(err.value) == "Missing value for argument 'arg1'."


def test_missing_required_option():
    with pytest.raises(ValueError) as err:
        build_command_string(command_required)

    assert str(err.value) == "Parameter 'required' is required."


def test_required_option():
    command_string = build_command_string(command_required, required=5)
    assert command_string == "command-required --required 5"


def test_narg2():
    command_string = build_command_string(command_nargs2, arg=[1, 2])
    assert command_string == "command-nargs2 1 2"


def test_narg2_incorrect_length():
    with pytest.raises(ValueError) as err:
        build_command_string(command_nargs2, arg=[1, 2, 3])
    assert str(err.value) == "Invalid number of arguments for parameter 'arg'."


def test_tuple_param():
    command_string = build_command_string(command_tuple, tuple_option=("bye", 3))
    assert command_string == "command-tuple --tuple-option bye 3"


def test_tuple_param_bad_format():
    with pytest.raises(ValueError) as err:
        build_command_string(command_tuple, tuple_option="bye,3")
    assert str(err.value) == "Value for parameter 'tuple_option' must be a tuple."


def test_tuple_param_bad_length():
    with pytest.raises(ValueError) as err:
        build_command_string(command_tuple, tuple_option=["hi", 3, "bye"])
    assert str(err.value) == "Value for parameter 'tuple_option' must have len 2."


def test_flag_value_default():
    command_string = build_command_string(command_flag_value, bias=True)
    assert command_string == "command-flag-value"


def test_flag_value_with_flag():
    command_string = build_command_string(command_flag_value, flat=True)
    assert command_string == "command-flag-value --flat"


def test_flag_value_with_groupper():
    command_string = build_command_string(command_flag_value, flavour="dark")
    assert command_string == "command-flag-value --dark"
