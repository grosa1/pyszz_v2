import subprocess
from typing import List

from packaging.version import parse


def run_cmd(cmd: List[str]):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = p.communicate()
    status = p.wait()

    if status != 0:
        raise Exception(stdout)

    return stdout.decode('utf-8')


def check_requirements():
    """
    * git >= 2.23

    * srcML (https://www.srcml.org/) (i.e., the srcml command should be in the system path)
    """

    # check git client
    required_git_version = "2.23.0"
    try:
        out = run_cmd(['git', '--version'])
        curr_git_version = out.split()[-1]
        if parse(curr_git_version) < parse(required_git_version):
            raise Exception()
    except:
        raise Exception(f"git client >= {required_git_version} is required. Please, fix")

    # check srcML
    try:
        run_cmd(['srcml', '--version'])
    except:
        raise Exception(f"srcML tool is required, and the 'srcml' command should be in the system path. Please, fix")