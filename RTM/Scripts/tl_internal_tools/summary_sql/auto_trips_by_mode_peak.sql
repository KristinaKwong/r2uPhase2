SELECT

    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(peak) as peak
    ,LOWER(mode) as mode
    ,'trips' as measure
    ,SUM(trips) as value

FROM autoTripsGy

GROUP BY
    (SELECT scenario FROM metadata) 
    ,(SELECT alternative FROM metadata) 
    ,(SELECT horizon_year FROM metadata)   
    ,UPPER(peak)
    ,LOWER(mode)
    ,'trips'
    

ORDER BY
    UPPER(peak)
    ,CASE WHEN mode = 'Sov' THEN 1
          WHEN mode = 'Hov' THEN 2
          WHEN mode = 'LGV' THEN 3
          WHEN mode = 'HGV' THEN 4
          ELSE 5
          END