#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-01-17
# @Filename: core.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import json

import typing as t

import click


__all__ = ["command_to_json", "build_command_string"]


def command_to_json(command: click.Command) -> str:
    """Generates a JSON representation of a click command."""

    click_params = command.params

    unclick_json = {"name": "", "parameters": {}, "required": [], "arguments": []}
    unclick_json["name"] = command.name

    for cparam in click_params:
        unclick_json["parameters"][cparam.name] = cparam.to_info_dict()
        if cparam.required:
            unclick_json["required"].append(cparam.name)
        if cparam.param_type_name == "argument":
            unclick_json["arguments"].append(cparam.name)

    return json.dumps(unclick_json, indent=2)


def _check_type(value: t.Any, param_info: dict[str, t.Any]):
    """Checks that a value has the correct type for a parameter."""

    name = param_info["name"]
    param_type = param_info["type"]["param_type"].lower()
    nargs = param_info["nargs"]

    python_type: type | tuple[type, ...]

    if value is None:
        return

    if param_type == "string":
        python_type = str
    elif param_type == "bool":
        python_type = bool
    elif param_type == "int":
        python_type = int
    elif param_type == "float":
        python_type = (float, int)
    elif param_type == "tuple":
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"Value for parameter {name!r} must be a tuple.")
        param_len = len(param_info["type"]["types"])
        if param_len != len(value):
            raise ValueError(f"Value for parameter {name!r} must have len {param_len}.")
        for ii, vv in enumerate(value):
            vv_info = param_info.copy()
            vv_info["nargs"] = 1
            vv_info["type"] = param_info["type"]["types"][ii]
            _check_type(vv, vv_info)
        return
    else:
        raise TypeError(f"click type {param_type} not supported.")

    test_values = [value] if not isinstance(value, (tuple, list)) else value

    if nargs != -1 and len(test_values) != nargs:
        raise ValueError(f"Invalid number of arguments for parameter {name!r}.")

    for test_value in test_values:
        if not issubclass(type(test_value), python_type):
            raise TypeError(
                f"Value {test_value!r} does not match type {param_type!r} "
                f"for parameter {name!r}."
            )


def parse_value(value: t.Any, param_info: dict[str, t.Any]):
    """Returns the string representation of a value for a certain parameter."""

    name = param_info["name"]
    param_type = param_info["type"]["param_type"].lower()
    is_argument = param_info["param_type_name"] == "argument"
    default = param_info.get("default", None)
    opts = param_info["opts"]

    if value is None:
        if is_argument:
            raise ValueError(f"'None' cannot be used as value for argument {name!r}.")
        return ""

    value_str: str

    if param_type in ["string", "int", "float"]:
        if param_type == "string":
            map_func = json.dumps  # For strings, always escape in quotes.
        else:
            map_func = str

        if isinstance(value, (tuple, list)):
            return " ".join(map(map_func, value))

        value_str = map_func(value)
        if not is_argument and value == default:
            return ""

    elif param_type == "bool":
        if is_argument:
            raise TypeError(f"Cannot process argument {name!r} of type bool.")

        if not param_info["is_flag"]:
            raise TypeError(f"Cannot process non-flag option {name!r} of type bool.")

        if value == default:
            return ""

        # Deal with options of the type --shout/--no-shout
        if param_info["secondary_opts"] != []:
            if value is True:
                return opts[0]
            else:
                return param_info["secondary_opts"][0]

        return opts[0]

    elif param_type == "tuple":
        value_str = " ".join(map(str, value))

    else:
        raise NotImplementedError(
            f"Cannot parse value for param {name!r} of type {param_type!r}."
        )

    if is_argument:
        return value_str

    opts[0]
    return f"{opts[0]} {value_str}"


def build_command_string(command_info: dict | str | click.Command, *args, **kwargs):
    """Builds a command string for a click command.

    This function takes a series of arguments and keywords arguments and
    returns a command string that can be used to invoke a click command.
    The parameter information for the click command must be passed as a
    JSON string (generally the output of `.command_to_json`). The command
    function itself can also be passed, in which case `.command_to_json` is
    called with the command.

    Positional arguments, ``args``, are used for the click command arguments,
    in the order in which they are defined. The keys of the keyword arguments,
    ``kwargs`` must match the names of the click options as defined in the
    information JSON.

    """

    if isinstance(command_info, click.Command):
        command_info = command_to_json(command_info)

    info_dict: dict[str, t.Any]

    if isinstance(command_info, str):
        info_dict = json.loads(command_info)
    else:
        info_dict = command_info

    command_string_template = "{command_name}{options}{arguments}"

    # First assign positional arguments to click command arguments.
    arguments = []

    n_arguments = len(info_dict["arguments"])
    args_required = [
        arg
        for arg in info_dict["arguments"]
        if info_dict["parameters"][arg]["required"] is True
    ]

    if n_arguments < len(args):
        raise ValueError("More arguments provided than expected.")

    if n_arguments > 0:
        for iarg in range(n_arguments):
            arg_name = info_dict["arguments"][iarg]

            # First check if we have not exhausted the positional arguments:
            if iarg <= len(args) - 1:
                value = args[iarg]
            else:
                # If the we have run out of positional arguments check if the argument
                # has been passed in as a keyword argument.
                if arg_name in kwargs:
                    value = kwargs[arg_name]
                else:
                    if arg_name in args_required:
                        raise ValueError(f"Missing value for argument {arg_name!r}.")
                    else:
                        continue

            param_info = info_dict["parameters"][arg_name]
            _check_type(value, param_info)
            arguments.append(parse_value(value, param_info))

    # Now let's move to the options. Loop over the keyword arguments and build the
    # options string.

    options = []

    for param_name in info_dict["parameters"]:
        if param_name in info_dict["arguments"]:
            # Already dealt with.
            continue

        param_info = info_dict["parameters"][param_name]

        if param_name not in kwargs:
            if param_info["required"] is True:
                raise ValueError(f"Parameter {param_name!r} is required.")
            else:
                continue

        value = kwargs.get(param_name, param_info["default"])
        _check_type(value, param_info)
        parsed = parse_value(value, param_info)

        if parsed != "":
            options.append(parsed)

    options_str = "" if len(options) == 0 else (" " + " ".join(options))
    arguments_str = "" if len(arguments) == 0 else (" " + " ".join(arguments))

    command_string = command_string_template.format(
        command_name=info_dict["name"],
        options=options_str,
        arguments=arguments_str,
    )

    return command_string.strip()
