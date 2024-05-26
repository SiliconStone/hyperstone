import setuptools

setuptools.setup(
    name='hyperstone',
    version='1.0.0',
    packages=setuptools.find_packages(include=['hyperstone*']),
    python_requires='>=3.8',
    install_requires=[
        'megastone==0.0.1',
        'unicorn>=1.0.2',
        'capstone>=5.0.1',
        'pyelftools>=0.30',
        'bincopy>=20.0.0',
        'setuptools>=68.2.0',
        'loguru>=0.7.2',
        'lief>=0.14.1',
        'cle>=9.2.102',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ]
)
