# Drom_ru_parser
My first python parser. It works with russian web-site drom.ru.

 You can:
   - Collect data in the target russian region
   - Collect cars by brand
   - Collect cars by brand and model

Required Libraries:
  - bs4
  - requests
  - numpy
  - pandas
  - os
  - re
  - time
  
  Start:
  In first you need a create datacash. If you have files: "all_cars_models.csv" and "region_data.csv", you can start to collect data. 
  Else, you need to call this methods "drom().get_region()", "drom().get_cars()".
  Those methods write files with actual lists of region, brands and models with links.
  You don't need to call those methods every time when you want to collect data.
  
  Collecting data:
  - if you need a catalog of all ads in region - use method "drom().collecter()".
  - If you need only links from target cars use "drom().get_data()". With data from ads you need put this method inside: "drom().merger()". 
   Example: "drom.merger(drom().get_data())"
  Collecting data is a long process, every time writes (or updates) a csv file with collected data.

Methods without arguments:
- drom().get_region() - creates a datadrame, contains a regions and their codes. 
- drom().get_cars() - creates a dataframe with catalog contains car brands, models and links

Methods with arguments:
- drom().collecter(code) - creates a catalog of ads in target region. Takes 1 argument. Integer, code of region (example Moscow's code is 77)
- drom().get_data(brand='All', model='all', city=77, page=100) - collects links of ads in catalog. Returns dataframe.
  - brand: str, arraylike object. Brandname of car looks like "bmw", "audi", "dodge" and etc. Argument 'All' collects data of all brands.
  - model: str, arraylike object. Modelname of car. Like "A4", "Volga", "Challenger". Argument 'All' collects data of all models.
  - city: int, str. Code or name of region
  - page: int - limit number of pages in collecting data
- drom().merger(dataframe) - returns a dataframe with unpacked links from data. Takes only dataframe contains links of ads.
