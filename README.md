# Air Raid Datasets

[Russia invaded Ukraine](https://war.ukraine.ua) on February 24, 2022.
This repository contains datasets with information about
the air raid sirens in Ukraine by each region.

There are two sources of alerts: official
and unofficial (collected by volunteers from [eTryvoga](https://app.etryvoga.com) channel).

Both datasets will be updated daily. All times are in UTC.

## Official dataset

You may see `datasets/official_data_en.csv` (🇬🇧) and `datasets/official_data_uk.csv` (🇺🇦) files.
They're identical but in different language.

Official dataset contains information from 15th of March 2022 – it's the first day when siren record occurs.

I'll extend soon with implementation from other sources from 24th of Feb until 15th of March 2022.

Official alerts has `source=official`, data from volunteers has `source=volunteer` (currently 0 records).

## Volunteer

Data by volunteers are stored in `datasets/volunteer_data_uk.csv` (🇺🇦) and (soon) in `datasets/volunteer_data_en.csv` (🇬🇧).

It contains more data (starts from 25th of February 2022 – second day of war!) and only on oblast (region) level.

If there are no messages about the end of the sirens,
you may see them with `naive=True` and `finished_at = started_at + 30 minutes`.

Thanks to [eTryvoga](https://app.etryvoga.com) channel for this data.


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

Then you may see created files in `/datasets/` directory.

### Data Source

Thanks to [eTryvoga](https://app.etryvoga.com) developers for implementing that useful telegram channel!

### Слава Україні! 🇺🇦
