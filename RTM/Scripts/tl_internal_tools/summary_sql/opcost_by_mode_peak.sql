SELECT

    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,UPPER(peakperiod) as peak
    ,SUM(Length * SOV * (SELECT autoOpCost FROM params)) as sov
    ,SUM(Length * HOV * (SELECT autoOpCost FROM params)) as hov
    ,SUM(Length * Light_Trucks * (SELECT lgvOpCost FROM params)) as lgv
    ,SUM(Length * Heavy_Trucks * (SELECT hgvOpCost FROM params)) as hgv

FROM netResults

GROUP BY
    (SELECT scenario FROM metadata)
    ,(SELECT alternative FROM metadata)
    ,(SELECT horizon_year FROM metadata)
    ,UPPER(peakperiod)