from setuptools import find_packages, setup

setup(
    name="telegram_gpt",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot",
        # добавьте другие зависимости здесь
    ],
)
