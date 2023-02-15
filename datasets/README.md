### About Datasets

There are two sources of alerts: official
and unofficial (collected by volunteers from [eTryvoga](https://app.etryvoga.com) channel).

Both datasets will be updated daily. All times are in UTC.

## Official dataset

You may see `official_data_en.csv` (🇬🇧) and `official_data_uk.csv` (🇺🇦) files.
They're identical but in different language.

Official dataset contains information from 15th of March 2022 – it's the first day when siren record occurs.

I'll extend soon with implementation from other sources from 24th of Feb until 15th of March 2022.

Official alerts has `source=official`, data from volunteers has `source=volunteer` (currently 0 records).

## Volunteer

Data by volunteers are stored in `volunteer_data_uk.csv` (🇺🇦) and (soon) in `volunteer_data_en.csv` (🇬🇧).

It contains more data (starts from 25th of February – second day of war!) and only on oblast (region) level.

If there are no messages about the end of the sirens,
you may see them with `naive=True` and `finished_at = started_at + 30 minutes`.

Thanks to [eTryvoga](https://app.etryvoga.com) channel for this data.
