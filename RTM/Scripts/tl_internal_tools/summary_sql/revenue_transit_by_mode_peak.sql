SELECT
    
    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(peak) as peak
    ,LOWER(mode) as mode
    ,'transit_revenue' as measure
    ,value

FROM transitRevenue

ORDER BY
    LOWER(mode)
    ,UPPER(peak)