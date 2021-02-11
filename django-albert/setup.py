import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-albert',
    version='2.18.10',
    packages=find_packages(),
    include_package_data=True,
    license='Proprietary License',  # example license
    description='Web application for albert app backend management.',
    long_description=README,
    url='http://www.thinkittwice.com/',
    author='ThinkItTwice',
    author_email='admin@thinkittwice.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: Proprietary License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'boto==2.49.0',
        'Django==1.11.26',
        'django-ckeditor==5.8.0',
        'django-nested-admin==3.2.4',
        'django-smart-selects==1.5.4',
        'django-storages==1.8',
        'django-suit==0.2.28',
        'django-redis==4.10.0',
        'django-model-utils==3.2.0',
        'django-environ==0.4.5',
        'isoweek==1.3.3',
        'mysqlclient==1.4.6',
        'Pillow==5.4.1',
        'python-monkey-business==1.0.0',
        'PyYAML==5.2',
        'six==1.13.0',
        'django-easy-select2==1.5.6',
        'python-dateutil==2.7.3',
        'requests==2.22.0',
        'django-rq==1.3.1',
        'rq==0.13.0',
        'redis==3.3.11',
        'pycountry==20.7.3',
        'django-phonenumber-field==4.0.0',
        'phonenumbers==8.12.8',
    ]
)
