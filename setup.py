from setuptools import setup, find_packages

setup \
(
    name = 'csv2txt',
    author = 'b3hav1',
    version = '0.1.0',
    packages = find_packages(),
    python_requires = '>=3.10',
    description = 'Converts CSV to the text table with box-drawing borders.',
)