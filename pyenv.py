import os
import pkg_resources
import argparse

try:
    from pip import main as pip_install
except:
    from pip._internal import main as pip_install
"""
Python script to build python project environment.

Responsibilities: 
    - check if a virtual environment exists on global python, if not it will install it - 
        - can change the virtual environment package name by setting the variable VENV

    - check the current platform (windows/linux/mac) and run corresponding requirements.txt file
        - requirements files names can be changed using these variables:
            - linux: variable: LINUX_REQUIREMENTS; default: requirement_linux.txt
            - windows: variable: WINDOWS_REQUIREMENTS; default: requirement_windows.txt
            - mac: variable: DARWIN_REQUIREMENTS; default: requirement_darwin.txt
            - all fallback default value to requirements.txt (in case the original default doesn't exist)
"""


def get_installed():
    """
    Gets the installed pacakages from pip pointed by current PATH
    :param local_only:
    :return:
    """
    pkg_resources._initialize_master_working_set()  # refresh installed packages TODO: find replacement
    return [d for d in pkg_resources.working_set]  # return working set as array


def get_requirements_content():
    requirements_path = None
    requirements_content = []
    from sys import platform
    if platform.startswith('win'):
        requirements_path = get_requirements_path(args.WINDOWS_REQUIREMENTS)
    if platform.startswith('linux'):
        requirements_path = get_requirements_path(args.LINUX_REQUIREMENTS)
    if platform == 'darwin':  # MacOS
        requirements_path = get_requirements_path(args.DARWIN_REQUIREMENTS)

    if os.path.exists(requirements_path) and os.path.isfile(requirements_path):
        print("using {} requirements file: {}".format(platform, requirements_path))
        with open(requirements_path) as f:
            requirements_content = f.readlines()
    else:
        print("Cannot find requirements file at: {}".format(requirements_path))

    return requirements_content


def get_requirements_path(requirements_filename):
    full_path = os.path.join(get_home(), requirements_filename)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        full_path = os.path.abspath(full_path)
    else:
        print("Unable to find {}, fallback to default {}".format(full_path, args.DEFAULT_REQUIREMENTS))
        full_path = os.path.join(get_home(), args.DEFAULT_REQUIREMENTS)

    return full_path


def install(packages):
    for package in packages:
        pip_install(['install', package])


def install_in_virtualenv():
    requirements_content = get_requirements_content()
    for package in requirements_content:
        pip_install(['install', "--prefix", get_env_path(), package])


def virtualenv_dist_info():
    virtualenv_info = None
    current_freeze = get_installed()

    for requirement in current_freeze:
        if args.PROVIDER in requirement.key:
            virtualenv_info = requirement

    return virtualenv_info


def get_home():
    if os.path.isfile(args.HOME_DIR):
        home = os.path.dirname(os.path.abspath(args.HOME_DIR))
    else:
        home = os.path.abspath(args.HOME_DIR)
    return home


def get_env_path():
    return os.path.join(get_home(), args.ENV_NAME)


def create_virtual_env(clear=False):
    home = get_env_path()
    if os.path.exists(home):
        if clear:
            print("Clearing and creating virtual environment at: {}".format(home))
        else:
            print("Updating virtual environment at: {}".format(home))
    else:
        print("Creating virtual environment at: {}".format(home))

    if args.PROVIDER == "virtualenv":
        import virtualenv
        virtualenv.create_environment(home, clear=clear)
    else:
        raise Exception("{} is not supported as environment provider".format(args.PROVIDER))


def freeze_env():
    env_path = get_env_path().lower()
    installed = [x for x in get_installed() if env_path in x.location.lower()]
    print("==================")
    print("pip freeze")
    for package in installed:
        print("\t{}=={}".format(package.key, package.version))
    print("==================")


def activate():
    from sys import platform
    activate_this_dir_name = "Scripts" if platform.startswith('win') else "bin"
    activate_script = os.path.join(get_env_path(), activate_this_dir_name, "activate_this.py")
    exec (open(activate_script).read(), dict(__file__=activate_script))


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="pyenv", description="Python virtualenv helper")
    parser.add_argument("-p", "--provider", help="virtual environment provider, ex:virtualenv", dest="PROVIDER",
                        default="virtualenv")
    parser.add_argument("--name", help="name of the virtual environment root dir", dest="ENV_NAME", default="env")
    parser.add_argument("--clear", help="whether to clear the existing env or not", default=True, dest="CLEAR")
    parser.add_argument("--project_dir", help="the full path to the root directory", dest="HOME_DIR",
                        default=os.path.abspath("."))

    parser.add_argument("-lin", "--lin_req", help="name of linux requirements file", dest="LINUX_REQUIREMENTS",
                        default="requirements_linux.txt")
    parser.add_argument("-win", "--win_req", help="name of windows requirements file", dest="WINDOWS_REQUIREMENTS",
                        default="requirements_windows.txt")
    parser.add_argument("-dar", "--dar_req", help="name of darwin requirements file", dest="DARWIN_REQUIREMENTS",
                        default="requirements_darwin.txt")
    parser.add_argument("--def_req", help="name of default requirements file", dest="DEFAULT_REQUIREMENTS",
                        default="requirements.txt")

    args = parser.parse_args()
    args.CLEAR = str2bool(args.CLEAR)
    virtualenv_data = virtualenv_dist_info()
    if virtualenv_data is None:
        print("no virtual environment provider installed, installing {}".format(args.PROVIDER))
        install([args.PROVIDER])
        virtualenv_data = virtualenv_dist_info()
        if virtualenv_data is None:
            raise Exception("Unable to install {}".format(args.PROVIDER))

    print("virtual environment provider is: {}".format(virtualenv_data.key))

    create_virtual_env(clear=args.CLEAR)

    activate()

    install_in_virtualenv()

    freeze_env()
