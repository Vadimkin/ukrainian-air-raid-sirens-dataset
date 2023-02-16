# Air Raid Datasets

[Russia invaded Ukraine](https://war.ukraine.ua) on February 24, 2022.
This repository contains datasets with information about
the air raid sirens in Ukraine by each region.


## Datasets
There are two sources of alerts: official
and unofficial (collected by volunteers from [eTryvoga](https://app.etryvoga.com) channel).

For additional information please look into [datasets/README.md](datasets/README.md) inside of datasets directory.


### How to regenerate .csv files

Datasets updated daily. If you still want to regenerate it manually, please follow these steps:

```shell
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cp config.py.EXAMPLE config.py
nano config.py # visit https://my.telegram.org/apps to retrive your app id and hash
python3 process.py
```

Then you may see created files in `/datasets/` directory.

### Слава Україні! 🇺🇦
