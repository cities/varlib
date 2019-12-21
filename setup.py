from codecs import open as codecs_open
from setuptools import setup, find_packages


# Get the long description from the relevant file
with codecs_open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(name='varlib',
      version='0.3.0',
      description=u"Variable Library",
      long_description=long_description,
      classifiers=[],
      keywords='',
      author=u"Liming Wang",
      author_email='',
      url='https://github.com/cities/varlib',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'click',
          'networkx',
          'numpy',
          'pandas',
          'pyyaml',
          'simpleeval',
          'xxhash',
      ],
      extras_require={
          'test': ['pytest'],
      },
      entry_points="""
      [console_scripts]
      varlib=varlib.scripts.cli:cli
      """
      )
