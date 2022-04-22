import subprocess
from io import StringIO
from typing import Optional

import click

from pyinfra import logger
from pyinfra.api.exceptions import InventoryError
from pyinfra.connectors.util import (
    read_buffers_into_queue,
    split_combined_output,
)

KEY_CONTAINER = "lxd_container"
EXECUTION_CONNECTOR = True


def make_names_data(
    hostname: Optional[str] = None,
) -> tuple[str, dict, list[str]]:
    if not hostname:
        raise InventoryError("No container specified")

    yield f"@lxd/{hostname}", {KEY_CONTAINER: hostname}, ["@lxd"]


def connect(state, host) -> bool:
    return True


def disconnect(state, host) -> bool:
    return True


def run_shell_command(
    state,
    host,
    command,
    get_pty=False,
    timeout=None,
    stdin=None,
    success_exit_codes=None,
    print_output=False,
    print_input=False,
    return_combined_output=False,
    use_sudo_password=False,
    **command_kwargs,
):
    """
    Execute a (shell) command on the target host.

    Args:
        state (``pyinfra.api.State`` object): state object for this command
        host (``pyinfra.api.Host`` object): the target host
        command (string): actual command to execute

    Returns:
        tuple: (exit_code, stdout, stderr)
        stdout and stderr are both lists of strings from each buffer.
    """
    container = host.data.get(KEY_CONTAINER)

    lxd_command = ["lxc", "exec", container, "--", "sh", "-c", str(command)]

    if print_input:
        click.echo(f"{host.print_prefix}>>> {lxd_command}")

    process = subprocess.Popen(
        lxd_command,
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    combined_output = read_buffers_into_queue(
        process.stdout,
        process.stderr,
        timeout=timeout,
        print_output=print_output,
        print_prefix=host.print_prefix,
    )

    logger.debug("--> Waiting for exit status...")
    process.wait()
    logger.debug("--> Command exit status: {0}".format(process.returncode))

    # Close any open file descriptors
    process.stdout.close()
    process.stderr.close()
    status_code = process.returncode

    success = status_code in (success_exit_codes or [0])
    if return_combined_output:
        return success, combined_output
    stdout, stderr = split_combined_output(combined_output)
    return success, stdout, stderr


def put_file(
    state,
    host,
    filename_or_io,
    remote_filename,
    print_output=False,
    print_input=False,
    **command_kwargs,
):
    """
    Upload a local file or IO object to the target host.

    Returns:
        status (boolean)
    """

    remote_path = f"{host.data.get(KEY_CONTAINER)}/{remote_filename}"
    if isinstance(filename_or_io, str):
        stdin = None
        lxd_command = ["lxc", "file", "push", filename_or_io, remote_path]
    else:
        stdin = filename_or_io
        lxd_command = ["lxc", "file", "push", "-", remote_path]
    text = isinstance(filename_or_io, (StringIO, str))

    if print_input:
        click.echo(f"{host.print_prefix}>>> {lxd_command}")

    process = subprocess.Popen(lxd_command, stdin=subprocess.PIPE, text=text)
    if stdin:
        stdin.seek(0)
        for chunk in stdin:
            process.stdin.write(chunk)
    process.stdin.close()

    logger.debug("--> Waiting for exit status...")
    process.wait()
    logger.debug("--> Command exit status: {0}".format(process.returncode))
    status_code = process.returncode

    return status_code == 0


def get_file(
    state,
    host,
    remote_filename,
    filename_or_io,
    print_output=False,
    print_input=False,
    **command_kwargs,
):
    """
    Download a remote file to a local file or IO object.

    Returns:
        status (boolean)
    """

    remote_path = f"{host.data.get(KEY_CONTAINER)}/{remote_filename}"
    if isinstance(filename_or_io, str):
        stdout = None
        lxd_command = ["lxc", "file", "pull", remote_path, filename_or_io]
    else:
        stdout = filename_or_io
        lxd_command = ["lxc", "file", "pull", remote_path, "-"]

    if print_input:
        click.echo(f"{host.print_prefix}>>> {lxd_command}")

    process = subprocess.Popen(lxd_command, stdout=stdout)
    stdout, stderr = process.communicate()
    process.wait()
    status_code = process.returncode

    return status_code == 0
