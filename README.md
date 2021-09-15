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
  In first you need a create datacash. If you haven't files: "all_cars_models.csv" and "region_data.csv". If you have, you can start to collect data.
  You need to intialize class Drom, and call this methods "drom.get_region()", "drom.get_cars()".
  Those methods write files with actual lists of region, brands and models with links.
  You don't need to call those methods every time when you want to collect data.
  
  Collecting data:
  - if you need a catalog of all ads in region - use method "drom.collecter()".
  - If you need only links from target cars use "drom.get_data()". With data from ads you need put this method inside: "drom.merger()". 
   Example: "drom.merger(drom.get_data())"
  Collecting data is a long process, every time writes (or updates) a csv file with collected data.
