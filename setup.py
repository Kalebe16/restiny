from setuptools import find_packages, setup

from data_fox.version import __version__

setup(
    name='data-fox',
    version=__version__,
    author='Kalebe Chimanski de Almeida',
    description='A minimalist API client with the cunning simplicity of a fox 🦊',
    entry_points={
        'console_scripts': [
            'data-fox=data_fox.__main__:main',
        ],
    },
    packages=find_packages(),
    package_data={'callmetrics_api': ['templates/**/*']},
    python_requires='>=3.9',
    install_requires=[
        'textual==0.75.1',
        'textual[syntax]',
        'httpx==0.27.2',
        'pyperclip==1.9.0',
    ],
)
