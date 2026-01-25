## 🚨 About Datasets

There are two sources of alerts: official
and unofficial (collected by volunteers from [eTryvoga](https://app.etryvoga.com) channel).

Both datasets will be updated daily. All times are in UTC.

### Official dataset

You may see `official_data_en.csv` (🇬🇧) and `official_data_uk.csv` (🇺🇦) files.
They're identical but in different language.

Official dataset contains information from 15th of March 2022 – it's the first day when siren record occurs.
Since December, 2025th there is mostly air raid alerts on raion (district) level ([see post in the media](https://texty.org.ua/fragments/116501/v-ukrayini-zaprovadzhuyetsya-novyj-pidxid-do-oholoshennya-povitryanyx-tryvoh-svyrydenko/)), before sirens were applied to the whole oblast (region). You may find them on [wikipedia](https://en.wikipedia.org/wiki/Raions_of_Ukraine).
On some .geojson files they're Subnational Administrative Boundaries (Admin 2: 139 Raion (District))

### Volunteer datasets

Data by volunteers are stored in `volunteer_data_uk.csv` (🇺🇦) and `volunteer_data_en.csv` (🇬🇧).

It contains more data (starts from 25th of February – second day of war!) and only on oblast (region) level.

If there are no messages about the end of the sirens,
you may see them with `naive=True` and `finished_at = started_at + 30 minutes`.

Thanks to [eTryvoga](https://app.etryvoga.com) channel for this data.

## 🤔 Good to Know

There are two permanent sirens:

1. In **Luhansk region** from April 4 at 04:45 PM (UTC+00) or April 4 at 07:45 PM (local time)
2. In **Crimea** from December 10 at 10:22 PM (UTC+00) or December 11 at 12:22 AM (local time)

They are not listed in datasets, so you may want to process them manually.
