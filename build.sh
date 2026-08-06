#!/usr/bin/env bash
# build.sh
# Sets up the virtual environment and compiles aio.py into a native executable using Cython.

set -e

# 1. Setup virtual environment and install requirements
echo "=== Step 1: Setting up Virtual Environment ==="
if [ ! -f "venv-build.sh" ]; then
    echo "Error: venv-build.sh not found."
    exit 1
fi

./venv-build.sh

echo "=== Step 2: Activating Virtual Environment ==="
source venv/bin/activate

# 2. Build via Cython
echo "=== Step 3: Compiling aio.py via Cython ==="

if ! command -v gcc &> /dev/null; then
    echo "Error: gcc is not installed. Please install build-essential or gcc to compile."
    exit 1
fi

# Cythonize with --embed to create a standalone C file with a main() function
echo "Generating C code with Cython..."
cython --embed -3 aio.py -o aio_bin.c

# Get the necessary C compiler flags and linker flags from the python environment
echo "Gathering compiler flags..."
CFLAGS=$(python3-config --cflags)
# In python 3.8+, --embed is required for ldflags to link libpython
LDFLAGS=$(python3-config --ldflags --embed 2>/dev/null || python3-config --ldflags)

# Compile using gcc
echo "Running gcc..."
gcc -O3 $CFLAGS aio_bin.c $LDFLAGS -o aio_bin

echo "=== Build Complete ==="
echo "Successfully built native executable: aio_bin"
echo "You can now run it independently (while the venv or required libs are present):"
echo "./aio_bin --help"
