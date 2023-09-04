import setuptools
with open("README.md", "r",encoding="utf-8") as f:
    long_description = f.read()
    
setuptools.setup(
    name = "Tpteropy",
    version = "0.0.2",
    author = "Tomycat",
    author_email="tangminghong.tom@gmail.com",
    description="簡單存取Pterodactyl api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TommcyOWO/Tpteropy",                                         
    packages=setuptools.find_packages(),     
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
    )
