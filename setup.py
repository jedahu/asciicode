from distutils.core import setup

setup(
    name='AsciiCode',
    version='0.1.0-SNAPSHOT',
    author='Jeremy Hughes',
    author_email='jed@jedatwork.com',
    packages=['asciicode'],
    url='https://github.com/jedahu/asciicode',
    license='GPL2',
    description='Simple quasi-literate programming tool.',
    long_description=open('README').read(),
    include_package_data=True
    )
