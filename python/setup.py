"""
this file is based on pyspark packaging - we have customized it for zingg
"""

import importlib.util
import os
import sys
from pathlib import Path
from setuptools import *
from shutil import copyfile, copytree, rmtree
from setuptools.command.install import install

class InstallCommand(install):
    def run(self):
        install.run(self)

def tidy_temp_links(IN_ZINGG):
    """
    Clean up directories created for previous or failed versions of the build.
    """
    to_remove = ["jars", "scripts", "models", "examples", "phases", "config"]
    if IN_ZINGG:
        for directory in to_remove:
            dead_path = Path("zingg", directory)
            if dead_path.exists():
                if os.name == "nt":
                    rmtree(dead_path)
                else:
                    dead_path.unlink()


# establish version
with open("VERSION.txt", "r") as _fh:
    __version__ = _fh.readline().strip()

# Establish ZINGG_HOME directory
ZINGG_HOME = os.path.abspath("../")

if not Path(ZINGG_HOME, "python", "install.py").exists():
    print(
        "Failed to load Zingg version file for packaging.",
        "Make sure you are in %s/python"%ZINGG_HOME,
        file=sys.stderr,
    )
    sys.exit(-1)
print("ZINGG_HOME is %", ZINGG_HOME)

# Import install.py
try:
    spec = importlib.util.spec_from_file_location("install", "install.py")
    install_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(install_module)
except IOError:
    print(
        "Failed to load required install module (install.py)",
        file=sys.stderr,
    )
    sys.exit(-1)

# Provide guidance about how to use setup.py
incorrect_invocation_message = """
If you are installing zingg from zingg source, you must build the Zingg jarfiles
before attempting to create the package with "setup.py build sdist"

To build zingg with maven you can run:

    $ZINGG_HOME/mvn -DskipTests clean package

Building the source dist is done in the Python directory:

    cd python
    python setup.py sdist
    pip install dist/*.tar.gz
"""

# Figure out where the jars are we need to package with zingg.
JARS_PATH = Path(ZINGG_HOME, "assembly", "target")

# No jars, no peace.
jar_jar_blanks = "No zingg jars found. Run 'mvn -DskipTests clean package' in $ZINGG_HOME before attempting to build the package, please."
if not JARS_PATH.exists():
    # Uh oh! Empty list!
    print(jar_jar_blanks, file=sys.stderr)
    sys.exit(-1)

print("jar path is ", JARS_PATH)

EXAMPLES_PATH = os.path.join(ZINGG_HOME, "examples")
SCRIPTS_PATH = os.path.join(ZINGG_HOME, "scripts")
DATA_PATH = os.path.join(ZINGG_HOME, "models")
CONF_PATH = os.path.join(ZINGG_HOME, "config")
PHASES_PATH = os.path.join(ZINGG_HOME, "python/phases")

SCRIPTS_TARGET = os.path.join("zingg", "scripts")
JARS_TARGET = os.path.join("zingg", "jars")
EXAMPLES_TARGET = os.path.join("zingg", "examples")
DATA_TARGET = os.path.join("zingg", "models")
CONF_TARGET = os.path.join("zingg", "config")
PHASES_TARGET = os.path.join("zingg", "phases")

# Check and see if we are under the Zingg path in which case we need to build
# the symlink farm. This is important because we only want to build the symlink
# farm while under Zingg otherwise we
# want to use the symlink farm. And if the symlink farm exists under while
# under Zingg (e.g. a partially built sdist) we should error and have the user
# sort it out.
IN_ZINGG = os.path.isfile("../core/src/main/java/zingg/Trainer.java") == 1

# assure we don't have junk files laying around
tidy_temp_links(IN_ZINGG)

try:

    os.makedirs("zingg", exist_ok=True)

    if IN_ZINGG:
        # Construct the symlink farm - this is necessary since we can't refer
        # to the path above the package root and we need to copy the jars and
        # scripts which are up above the python root.
        if os.name == "posix":
            os.symlink(JARS_PATH, JARS_TARGET)
            os.symlink(SCRIPTS_PATH, SCRIPTS_TARGET)
            os.symlink(EXAMPLES_PATH, EXAMPLES_TARGET)
            os.symlink(DATA_PATH, DATA_TARGET)
            os.symlink(CONF_PATH, CONF_TARGET)
            os.symlink(PHASES_PATH, PHASES_TARGET)
        else:
            # For windows fall back to the slower copytree
            copytree(JARS_PATH, JARS_TARGET)
            copytree(SCRIPTS_PATH, SCRIPTS_TARGET)
            copytree(EXAMPLES_PATH, EXAMPLES_TARGET)
            copytree(DATA_PATH, DATA_TARGET)
            copytree(CONF_PATH, CONF_TARGET)
            copytree(PHASES_PATH, PHASES_TARGET)
    else:
        # If we are not inside of ZINGG_HOME verify we have the required symlink farm
        if not os.path.exists(JARS_TARGET):
            print(
                "To build packaging must be in the python directory under the ZINGG_HOME.",
                file=sys.stderr,
            )

    if not os.path.isdir(SCRIPTS_TARGET):
        print(incorrect_invocation_message, file=sys.stderr)
        sys.exit(-1)

    # Scripts directive requires a list of each script path and does not take wild cards.
    script_names = os.listdir(SCRIPTS_TARGET)
    scripts = list(
        map(lambda script: os.path.join(SCRIPTS_TARGET, script), script_names)
    )

    packages = []
    packages.append("zingg")
    # packages.append('zingg.pipes')

    with open("README.md") as f:
        long_description = f.read()

    setup(
        name="zingg",
        version=__version__,
        author="Zingg.AI",
        author_email="sonalgoyal4@gmail.com",
        description="Zingg Entity Resolution, Data Mastering and Deduplication",
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        url="https://github.com/zinggAI/zingg",
        # packages=find_packages(),
        packages=packages,
        package_dir={
            "zingg.jars": "zingg/jars",
            "zingg.scripts": "zingg/scripts",
            "zingg.data": "zingg/models",
            "zingg.examples": "zingg/examples",
            "zingg.conf": "zingg/config",
            "zingg.phases": "zingg/phases",
        },
        package_data={
            "zingg.jars": ["*.jar"],
            "zingg.scripts": ["*"],
            "zingg.data": ["*"],
            "zingg.examples": ["*.py", "*/examples/*.py"],
            "zingg.conf": ["*"],
            "zingg.phases": ["*"],
            "": ["*.py"],
            "": ["LICENCE"],
        },
        include_package_data=True,
        scripts=scripts,
        license="http://www.apache.org/licenses/LICENSE-2.0",
        install_requires=[
            "py4j==0.10.9",
            "numpy",
            "pandas",
            "pyspark",
        ],
        extras_require={"zingg": ["pyspark>=3.1.2"]},
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: GNU Affero General Public License v3",
            "Operating System :: OS Independent",
        ],
        zip_safe=False,
        keywords="Entity Resolution, deduplication, record linkage, data mastering, identity resolution",
        cmdclass={"install": InstallCommand,},
    )

finally:
    tidy_temp_links(IN_ZINGG)



