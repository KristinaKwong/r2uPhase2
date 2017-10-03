SELECT 

    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(period) as peak
    ,LOWER(mode) as mode
    ,'ridership' as measure
    ,SUM(trips) as value

FROM daily_gy

WHERE 1=1
    and mode in ('bus','rail','wce')

GROUP BY
    (SELECT scenario FROM metadata)
    ,(SELECT alternative FROM metadata)
    ,(SELECT horizon_year FROM metadata)
    ,UPPER(period)
    ,LOWER(mode)
    ,'ridership'
