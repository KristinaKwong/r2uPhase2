SELECT

    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(peakperiod) as peak
    ,SUM(CASE WHEN speed < losDspeed THEN Length * SOV ELSE 0 END) as sov
    ,SUM(CASE WHEN speed < losDspeed THEN Length * HOV ELSE 0 END) as hov
    ,SUM(CASE WHEN speed < losDspeed THEN Length * Light_Trucks ELSE 0 END) as lgv
    ,SUM(CASE WHEN speed < losDspeed THEN Length * Heavy_Trucks ELSE 0 END) as hgv

FROM netResults

GROUP BY
    (SELECT scenario FROM metadata)
    ,(SELECT alternative FROM metadata)
    ,(SELECT horizon_year FROM metadata)
    ,UPPER(peakperiod)