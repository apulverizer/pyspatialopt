from distutils.core import setup

setup(name='PySpatialOpt',
    version='0.0.1',
    description='Python Spatial Optimization Library',
    author='Aaron Pulver',
    author_email='apulverizer@gmail.com',
    url='https://github.com/apulverizer/pyspatialopt',
    packages=['pyspatialopt', 'pyspatialopt.models',
              'pyspatialopt/analysis'],
    license='MIT',
    install_requires=['pulp>=1.6.1'],
    classifiers=[
      'Intended Audience :: Developers/Researchers',
      'Programming Language :: Python :: 2.7'
    ]
 )
