# Air Raid Dataset 

[Russia invaded Ukraine](https://war.ukraine.ua) on February 24, 2022.
This repository contains dataset file `air-raid-dataset.csv` with information about
the air raid sirens in Ukraine by each region.

### Good to know

`.csv` contains columns with region name, air raid siren started time, ended time and `naive` boolean value.

If there are no messages about the end of the sirens, `naive` column
will be `True` and `finished_at` will be `started_at + 30 minutes`.

All times are in UTC.


### How to regenerate .csv file

This file is already added to the repo. If you want to generate it manually, please follow these steps:

```shell
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cp config.py.EXAMPLE config.py
nano config.py # visit https://my.telegram.org/apps to retrive your app id and hash
python3 process.py
```

Then `air-raid-dataset.csv` will be generated.

### Data Source

Thanks to [eTryvoga](https://app.etryvoga.com) developers for implementing that useful telegram channel!

### Слава Україні! 🇺🇦
