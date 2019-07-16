import setuptools

with open('README.md') as file:

    readme = file.read()

name = 'shucks'

version = '0.1.0'

author = 'Exahilosys'

url = f'https://github.com/{author}/{name}'

setuptools.setup(
    name = name,
    version = version,
    author = author,
    url = url,
    packages = setuptools.find_packages(),
    license = 'MIT',
    description = 'Mini schema validator.',
    long_description = readme,
    long_description_content_type = 'text/markdown'
)
