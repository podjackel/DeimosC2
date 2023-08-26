#!/usr/bin/env python3

import argparse, sys, os, tarfile, subprocess
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile
from distutils.dir_util import copy_tree
from shutil import copyfile, rmtree



# Arguments
parser = argparse.ArgumentParser(description="This tool copies the DeimosC2 folders and files for distribution.")

parser.add_argument("-src", "--src",
                  help="This option takes in the source of the original folders and files")
parser.add_argument("-dst", "--dst",
                  help="This option takes in the destination to place the folders and files (e.g. C:/users/test/)")
parser.add_argument("-govers", "--govers",
                  help="Version of Golang to grab (e.g. 1.14.1)")
parser.add_argument("-system", "--system",
                  help="OS to compile for (lin, win, mac, all)")             

# Check to ensure at least one argument has been passed
if len(sys.argv)==1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()


def main():
    # Source and Destination variables
    source = args.src
    dest = args.dst

    # OS to compile for
    system = args.system
    
    # Go Version (e.g. 1.14.1)
    golang = args.govers

    # Create the directories for each system
    print("Creating Directories")
    fullpath = create_folders(system,dest)

    # Create gopath and goroot directories for each system
    print("Creating Go Directories")
    create_go_folders(fullpath)

    # Call copy function
    print("Copying Directories")
    copy_data(source,fullpath)

    # Call get_go function
    print("Grabbing Go")
    get_go(system,golang,fullpath)

    # Get go depedencies
    print("Grabbing Go Dependiencies")
    get_go_deps(fullpath)

    # Compile C2
    print("Compiling the C2")
    compile_C2(system,source,fullpath, golang)

    # Clean up if needed
    if system != "all" and os.path.exists(fullpath[0]+"/goTemp") == True:
        print("Cleaning up before zipping")
        rmtree(fullpath[0]+"/goTemp")

    # Zip up the packages
    print("Zipping up the packages")
    zip_files(system,fullpath)


# Create folders for each OS type chosen
def create_folders(system, dest):
    if system == "win":
        dirs = ["/DeimosC2_windows"]
    elif system == "lin":
        dirs = ["/DeimosC2_linux"]
    elif system == "mac":
        dirs = ["/DeimosC2_darwin"]
    elif system == "all":
        dirs = ["/DeimosC2_windows", "/DeimosC2_linux", "/DeimosC2_darwin"]

    full_paths = []
    for i in dirs:
        # Check to see if the path exists. If not create it
        if os.path.exists(dest+i) == False:
            os.mkdir(dest+i)
        # Append full path to full path list
        full_paths.append(dest+i)
    return full_paths

# Create nested folders for gopath and goroot
def create_go_folders(fullpath):
    folders = ["/goroot", "/gopath"]
    for p in fullpath:
        for i in folders:
            # Check to see if the path exists. If not create it
            if os.path.exists(p+i) == False:
                os.mkdir(p+i)

# Copy the folders and files from source to new location
def copy_data(source, fullpath):
    folders = ["/agents", "/archives", "/droppers", "/lib", "/modules", "/resources"]
    files = ["/requirements.txt", "/go.mod", "/go.sum"]
    # Copy folders into agents and destination
    for p in fullpath:
        for f in folders:
            copy_tree(source+f, p+f)
        for i in files:
            copyfile(source+i, p+i)


# Get the version of Golang we are supporting
def get_go(system, golang, fullpath):
    if system == "win":
        # Windows Zip File and save in Windows location
        print("Saving Golang Windows")
        winzipurl = "https://dl.google.com/go/go"+golang+".windows-amd64.zip"
        with urlopen(winzipurl) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zfile:
                zfile.extractall(fullpath[0]+"/goroot")
    elif system == "lin":
        # Linux and Mac tar.gz and save in respective locations
        print("Saving Golang Linux")
        linzipurl = "https://dl.google.com/go/go"+golang+".linux-amd64.tar.gz"
        with urlopen(linzipurl) as zipresp:
            with tarfile.open(fileobj=BytesIO(zipresp.read()), mode="r:gz") as tzfile:
                tzfile.extractall(fullpath[0]+"/goroot")
    elif system == "mac":
        print("Saving Golang Mac")
        maczipurl = "https://dl.google.com/go/go"+golang+".darwin-amd64.tar.gz"
        with urlopen(maczipurl) as zipresp:
            with tarfile.open(fileobj=BytesIO(zipresp.read()), mode="r:gz") as tzfile:
                tzfile.extractall(fullpath[0]+"/goroot")
    elif system == "all":
        # Windows Zip File and save in Windows location
        print("Saving Golang Windows")
        winzipurl = "https://dl.google.com/go/go"+golang+".windows-amd64.zip"
        with urlopen(winzipurl) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zfile:
                zfile.extractall(fullpath[0]+"/goroot")

        # Linux and Mac tar.gz and save in respective locations
        print("Saving Golang Linux")
        linzipurl = "https://dl.google.com/go/go"+golang+".linux-amd64.tar.gz"
        with urlopen(linzipurl) as zipresp:
            with tarfile.open(fileobj=BytesIO(zipresp.read()), mode="r:gz") as tzfile:
                tzfile.extractall(fullpath[1]+"/goroot")

        print("Saving Golang Mac")
        maczipurl = "https://dl.google.com/go/go"+golang+".darwin-amd64.tar.gz"
        with urlopen(maczipurl) as zipresp:
            with tarfile.open(fileobj=BytesIO(zipresp.read()), mode="r:gz") as tzfile:
                tzfile.extractall(fullpath[2]+"/goroot")

# Get required GO dependencies for agent compiling
def get_go_deps(fullpath):
    print("Get GO Dependencies")
    for p in fullpath:
        print("Getting golang/sys")
        golang_sys_path = p+"/gopath/src/golang.org/x/sys"
        if os.path.exists(golang_sys_path) == False:
            os.makedirs(golang_sys_path)
        subprocess.call("git clone https://github.com/golang/sys.git "+golang_sys_path, shell=True)

# Function to get temp directory if required
def temp_go(fullpath, golang):
    # Create temp folder for temp go binary
    os.mkdir(fullpath[0]+"/goTemp")

    # For temp go downloading we need to know what OS we are running to pull the right one
    if sys.platform.startswith('win32'):
        go_temp_binary = "https://dl.google.com/go/go"+golang+".windows-amd64.zip"
        print("Saving Temp Golang for Compiling")
        with urlopen(go_temp_binary) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zfile:
                zfile.extractall(fullpath[0]+"/goTemp")
    else:
        if sys.platform.startswith('linux'):
            go_temp_binary = "https://dl.google.com/go/go"+golang+".linux-amd64.tar.gz"
        elif sys.platform.startswith('darwin'):
            go_temp_binary = "https://dl.google.com/go/go"+golang+".darwin-amd64.tar.gz"
        print("Saving Temp Golang for Compiling")
        with urlopen(go_temp_binary) as zipresp:
            with tarfile.open(fileobj=BytesIO(zipresp.read()), mode="r:gz") as tzfile:
                tzfile.extractall(fullpath[0]+"/goTemp")

# Compile the C2 into the three supported platforms (Windows, Linux, Darwin)
def compile_C2(system, source, fullpath, golang):
    # Compile based on the OS chosen during runtime
    if system == "win":
        # Check if system that is running is windows or not
        # If not grab go for windows and then delete it after compile
        if sys.platform != "win32":
            # Grab temp golang
            temp_go(fullpath, golang)
            
            # Set go binary
            go_binary = fullpath[0]+"/goTemp/go/bin/go"
        else:
            # Set go binary
            go_binary = fullpath[0]+"/goroot/go/bin/go"

        print("Setting Environment Variables for DeimosC2 for Windows")
        my_env = os.environ.copy()
        my_env["GOPATH"] = fullpath[0]+"/gopath"
        my_env["GOOS"] = "windows"
        my_env["GOARCH"] = "amd64"
        print("Compiling DeimosC2 for Windows")
                
        subprocess.call(go_binary + " get github.com/lucas-clemente/quic-go", env=my_env, shell=True)
        my_env = os.environ.copy()
        my_env["GOOS"] = "windows"
        my_env["GOARCH"] = "amd64"
        subprocess.call(go_binary+" build -ldflags=\"-s -w\" -trimpath -o "+fullpath[0]+"/DeimosC2.exe "+source+"/c2/main.go", cwd=source, env=my_env, shell=True)
    elif system == "lin":
        # Check if system that is running is linux or not
        # If not grab go for linux and then delete it after compile
        if sys.platform != "linux":
            # Grab temp golang
            temp_go(fullpath, golang)
            
            # Set go binary
            go_binary = fullpath[0]+"/goTemp/go/bin/go"
        else:
            # Set go binary
            go_binary = fullpath[0]+"/goroot/go/bin/go"

        # Compiling C2 for Linux
        print("Setting Environment Variables for DeimosC2 for Linux")
        # Setting environment variables for go build
        my_env = os.environ.copy()
        my_env["GOPATH"] = fullpath[0]+"/gopath"
        my_env["GOOS"] = "linux"
        my_env["GOARCH"] = "amd64"
        print("Compiling DeimosC2 for Linux")
        subprocess.call(go_binary + " get github.com/lucas-clemente/quic-go", env=my_env, shell=True)
        my_env = os.environ.copy()
        my_env["GOOS"] = "linux"
        my_env["GOARCH"] = "amd64"
        subprocess.call(go_binary+" build -ldflags=\"-s -w\" -trimpath -o "+fullpath[0]+"/DeimosC2 "+source+"/c2/main.go", cwd=source, env=my_env, shell=True)
    elif system == "mac":
        # Check if system that is running is linux or not
        # If not grab go for linux and then delete it after compile
        if sys.platform != "darwin":
            # Grab temp golang
            temp_go(fullpath, golang)
            
            # Set go binary
            go_binary = fullpath[0]+"/goTemp/go/bin/go"
        else:
            # Set go binary
            go_binary = fullpath[0]+"/goroot/go/bin/go"

        # Compiling C2 for Mac
        print("Setting Environment Variables for DeimosC2 for Mac")
        # Setting environment variables for go build
        my_env = os.environ.copy()
        my_env["GOPATH"] = fullpath[0]+"/gopath"
        my_env["GOOS"] = "darwin"
        my_env["GOARCH"] = "amd64"
        print("Compiling DeimosC2 for Mac")
        subprocess.call(go_binary + " get github.com/lucas-clemente/quic-go", env=my_env, shell=True)
        my_env = os.environ.copy()
        my_env["GOOS"] = "darwin"
        my_env["GOARCH"] = "amd64"
        subprocess.call(go_binary+" build -ldflags=\"-s -w\" -trimpath -o "+fullpath[0]+"/DeimosC2 "+source+"/c2/main.go", cwd=source, env=my_env, shell=True)
    elif system == "all":
        # Get current OS to specify which go binary to use to compile
        if sys.platform.startswith('win32'):
            go_binary = fullpath[0]+"/goroot/go/bin/go"
        elif sys.platform.startswith('linux'):
            go_binary = fullpath[1]+"/goroot/go/bin/go"
        elif sys.platform.startswith('darwin'):
            go_binary = fullpath[2]+"/goroot/go/bin/go"

        # Compiling C2 for Windows
        print("Setting Environment Variables for DeimosC2 for Windows")
        # Setting environment variables for go build
        my_env = os.environ.copy()
        my_env["GOOS"] = "windows"
        my_env["GOARCH"] = "amd64"
        print("Compiling DeimosC2 for Windows")
        subprocess.call(go_binary+" build -ldflags=\"-s -w\" -trimpath -o "+fullpath[0]+"/DeimosC2.exe "+source+"/c2/main.go", cwd=source, env=my_env, shell=True)

        # Compiling C2 for Linux
        print("Setting Environment Variables for DeimosC2 for Linux")
        # Setting environment variables for go build
        my_env = os.environ.copy()
        my_env["GOOS"] = "linux"
        my_env["GOARCH"] = "amd64"
        print("Compiling DeimosC2 for Linux")
        subprocess.call(go_binary+" build -ldflags=\"-s -w\" -trimpath -o "+fullpath[1]+"/DeimosC2 "+source+"/c2/main.go", cwd=source, env=my_env, shell=True)

        # Compiling C2 for Mac
        print("Setting Environment Variables for DeimosC2 for Mac")
        # Setting environment variables for go build
        my_env = os.environ.copy()
        my_env["GOOS"] = "darwin"
        my_env["GOARCH"] = "amd64"
        print("Compiling DeimosC2 for Mac")
        subprocess.call(go_binary+" build -ldflags=\"-s -w\" -trimpath -o "+fullpath[2]+"/DeimosC2 "+source+"/c2/main.go", cwd=source, env=my_env, shell=True)

# Zip the packages up for distribution
def zip_files(system, fullpath):
    if system != "all":
        # Zipping the package
        zf = ZipFile(fullpath[0]+".zip", "w")
        abs_src = os.path.abspath(fullpath[0])
        for dirname, subdirs, files in os.walk(fullpath[0]):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
        zf.close()
    elif system == "all":
        # Zipping Windows
        zf = ZipFile(fullpath[0]+".zip", "w")
        abs_src = os.path.abspath(fullpath[0])
        for dirname, subdirs, files in os.walk(fullpath[0]):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
        zf.close()

        # Zipping Linux
        zf = ZipFile(fullpath[1]+".zip", "w")
        abs_src = os.path.abspath(fullpath[1])
        for dirname, subdirs, files in os.walk(fullpath[1]):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
        zf.close()

        # Zipping Mac
        zf = ZipFile(fullpath[2]+".zip", "w")
        abs_src = os.path.abspath(fullpath[2])
        for dirname, subdirs, files in os.walk(fullpath[2]):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
        zf.close()

if __name__ == "__main__":
    main()