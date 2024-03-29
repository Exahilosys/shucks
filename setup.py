import setuptools

with open('README.rst') as file:

    readme = file.read()

name = 'shucks'

version = '1.3.0'

author = 'Exahilosys'

url = f'https://github.com/{author}/{name}'

setuptools.setup(
    name = name,
    version = version,
    author = author,
    url = url,
    packages = setuptools.find_packages(),
    license = 'MIT',
    description = 'Quick schema validator.',
    long_description = readme
)
