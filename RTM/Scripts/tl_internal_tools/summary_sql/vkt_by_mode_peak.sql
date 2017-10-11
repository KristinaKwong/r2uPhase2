SELECT

    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(peakperiod) as peak
    ,SUM(Length * SOV) as sov
    ,SUM(Length * HOV) as hov
    ,SUM(Length * Light_Trucks) as lgv
    ,SUM(Length * Heavy_Trucks) as hgv

FROM netResults

GROUP BY
    (SELECT scenario FROM metadata)
    ,(SELECT alternative FROM metadata)
    ,(SELECT horizon_year FROM metadata)
    ,UPPER(peakperiod)