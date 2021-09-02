import pathlib

from setuptools import setup, find_packages


def parse_requirements(requirements_file):
    with open(requirements_file) as req:
        return req.read().strip().split('\n')


def get_pkgdata():
    data = {}
    with open("pkgdata.txt") as f:
        lines = f.readlines()
    for row in lines:
        row_s = str(row).strip()
        if not row_s.startswith("#"):
            key = row_s.split("=")[0]
            value = row_s.split("=")[1]
            data[key] = value
    return data


here = pathlib.Path(__file__).parent.resolve()
pkgdata = get_pkgdata()
print(pkgdata)

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')
package_name = pkgdata["package.name"]
package_version = pkgdata["package.version"]


setup(
    name=package_name,
    version=package_version,
    description='A library for handling M3U playlists for IPTV (AKA m3u_plus)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Beer4Ever83/ipytv',
    author='Francesco Rainone',
    author_email='beer4evah@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Multimedia :: Video',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    license='MIT',
    keywords='m3u, m3u_plus, iptv, playlist',
    package_dir={'ipytv': 'ipytv'},
    packages=find_packages(where='.', exclude=['tests']),
    python_requires='>=3.6, <4',
    install_requires=parse_requirements("requirements.txt"),
    extras_require={},
    package_data={},
    data_files=[],
    entry_points={},
    project_urls={
        'Bug Reports': 'https://github.com/Beer4Ever83/ipytv/issues',
        'Funding': 'https://www.buymeacoffee.com/beer4ever83',
        'Source': 'https://github.com/Beer4Ever83/ipytv',
    },
)
