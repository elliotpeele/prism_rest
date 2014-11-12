import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'prism_core',
    ]

setup(name='prism_rest',
      version='0.0',
      description='prism_rest',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Elliot Peele',
      author_email='elliot@bentlogic.net',
      url='https://github.com/elliotpeele/prism_rest',
      keywords='web wsgi bfg pylons pyramid rest',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='prism_rest',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = prism_rest:main
      """,
      )
