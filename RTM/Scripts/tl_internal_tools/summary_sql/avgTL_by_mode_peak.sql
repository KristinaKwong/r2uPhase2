SELECT
    
    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(period) as peak
    ,LOWER(mode) as mode
    ,CASE WHEN measure = 'mins' THEN 'avgTL_mins'
          WHEN measure = 'kms' THEN 'avgTL_kms'
          ELSE 'avgTL'
          END measure
    ,value

FROM avgTravelTimes

ORDER BY
    UPPER(period)
    ,CASE WHEN mode = 'Sov' THEN 1
          WHEN mode = 'Hov' THEN 2
          WHEN mode = 'LGV' THEN 3
          WHEN mode = 'HGV' THEN 4
          ELSE 5
          END