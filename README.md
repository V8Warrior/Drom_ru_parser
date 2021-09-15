# Drom_ru_parser
My first python parser. It works with russian web-site drom.ru.

 You can:
   - Collect data in the target russian region
   - Collect only cars by brand
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
  In first you need a create datacash. 
  You need to intialize class Drom, and call this methods ".get_region()", ".get_cars()".
  Those methods write files with actual lists of region, brands and models with links.
  You don't need to call those methods every time when you want to collect data.
  
  Collecting data:
 
    
  Collecting data from region is a long process, every se writes (or updates) a csv file with 
