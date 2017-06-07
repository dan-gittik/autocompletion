import setuptools


package = dict(
    name             = 'autocompletion',
    version          = '0.1.0',
    author           = 'Dan Gittik',
    author_email     = 'dan.gittik@gmail.com',
    description      = 'A Bash autocompletion framework implemented in Python.',
    license          = 'MIT',
    url              = 'https://github.com/dan-gittik/autocompletion',
    packages         = setuptools.find_packages(),
    install_requires = [
    ],
    tests_require    = [
        'pytest',
    ],
)


if __name__ == '__main__':
	setuptools.setup(**package)
