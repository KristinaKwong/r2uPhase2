SELECT

    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(peakperiod) as peak
    ,SUM(Auto_Time / 60 * SOV) as sov
    ,SUM(Auto_Time / 60 * HOV) as hov
    ,SUM(Auto_Time / 60 * Light_Trucks) as lgv
    ,SUM(Auto_Time / 60 * Heavy_Trucks) as hgv

FROM netResults

GROUP BY
    (SELECT scenario FROM metadata)
    ,(SELECT alternative FROM metadata)
    ,(SELECT horizon_year FROM metadata)
    ,UPPER(peakperiod)