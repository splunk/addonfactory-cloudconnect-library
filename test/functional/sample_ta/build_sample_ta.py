import sys
import os
import subprocess
import re
import getopt

def print_help():
    print("""
    This script will be helpful to build the sample TA with all the required 3rd party packages to test the functionality of cloudconnectlib. The add-on package will be provided as the output of this script which the user can install on the Splunk instance directly.\n
    Usage:
        build_sample_ta.py <sample_ta_name> <python_version_support>

        <sample_ta_name>              All the sample TAs are located in cloudconnectlib repo at location: test/functional/sample_ta.
                                      Provide name of the TA which needs to be built.
        <python_version_support>      Python version to be supported in the add-on. Allowed values are "python2" and "python3". 
                                      Default value is "python2"
                                      If "python2" is provided, then the add-on will support only Python2 version.
                                      If "python3" is provided, then the add-on will support only Python3 version
    """)
    pass


def parse_arguments():
    python_support = "python2"

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print_help()
        print("\nerror: Invalid command provided")
        sys.exit(2)

    sample_ta_name = sys.argv[1]
    if not os.path.isdir(sample_ta_name):
        print_help()
        print("\nerror: No such directory available: {}".format(sample_ta_name))
        sys.exit(2)

    sample_ta_name = sample_ta_name.rstrip("/")

    if len(sys.argv) == 3:
        python_support = str(sys.argv[2]).strip()
        if python_support not in ["python2", "python3"]:
            print_help()
            print("\nerror: Invalid value provided to mention the python version to be supported. Valid values are 'python2' and 'python3'")
            sys.exit(2)

    return (sample_ta_name, python_support)


def download_3rd_party_packages(current_dir):
    print("Downloading 3rd party packages...")
    os.chdir(os.path.join(current_dir, "..", "..", ".."))
    install_package_cmd = ["python", "install_packages.py"]
    install_package_proc = subprocess.Popen(install_package_cmd, shell=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    install_package_proc_output, err = install_package_proc.communicate()

    if err:
        if isinstance(err, bytes):
            err = err.decode()
        if err.__contains__("DEPRECATION: Python 2.7 will reach the end of its life"):
            print("3rd party packages downloaded successfully")
            return True
        else:
            print("Error occurred while downloading 3rd party packages.Error: {}".format(err))
            return False
    else:
        print("3rd party packages downloaded successfully")
        return True

def transfer_3rd_party_pkg(sample_ta_name, support_python_version):
    print("Transferring the 3rd party packages to sample TA...")
    package_destination_path = os.path.join("test", "functional", "sample_ta", sample_ta_name, "bin", sample_ta_name.lower())

    for package_name in os.listdir("package"):
        if support_python_version == "python3" and package_name in ["httplib2", "functools32", "concurrent"]:
            continue

        transfer_package_cmd = ["cp", "-rf", os.path.join("package", package_name), package_destination_path]
        transfer_task_proc = subprocess.Popen(transfer_package_cmd, shell=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        transfer_task_proc_output, transfer_task_err = transfer_task_proc.communicate()
        if isinstance(transfer_task_err, bytes):
            transfer_task_err = transfer_task_err.decode()

        if "" != transfer_task_err:
            print("Error while transfering 3rd packages to the Sample TA '{}'. Error: {}".format(sample_ta_name, transfer_task_err))
            return False

    print("3rd party packages transferred successfully to sample TA '{}'".format(sample_ta_name))
    return True

def archive_ta(sample_ta_name, current_dir):
    print("Archiving the TA...")
    archive_file_name = "{}.tar.gz".format(sample_ta_name)
    os.chdir(current_dir)
    cmd = ["tar", "-pczf", archive_file_name, sample_ta_name]
    archive_task_proc = subprocess.Popen(cmd, shell=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    archive_task_proc_output, archive_task_err = archive_task_proc.communicate()

    if isinstance(archive_task_err, bytes):
        archive_task_err = archive_task_err.decode()

    if "" != archive_task_err:
        print("Error while archiving the Sample TA '{}'. Error: {}".format(sample_ta_name, archive_task_err))
        return False
    else:
        print("Archived the Sample TA '{}'. Archived file path: {}".format(sample_ta_name, os.path.join(current_dir, archive_file_name)))

    return True



sample_ta_name, support_python_version = parse_arguments()

current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(current_dir,"..","..",".."))

download_status = download_3rd_party_packages(current_dir)

if not download_status:
    sys.exit(2)

transfer_status = transfer_3rd_party_pkg(sample_ta_name, support_python_version)

if not transfer_status:
    sys.exit(2)

archive_status = archive_ta(sample_ta_name, current_dir)

print("==========================================================")
if not archive_status:
    print("\nStatus: Failure")
else:
    print("\nStatus: Success")
print("\n=========================================================")