SELECT
    
    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,'DAILY' as peak
    ,'auto' as mode
    ,'parking_paid' as measure
    ,SUM(parking_paid) as value

FROM parkingPaid

GROUP BY
    (SELECT scenario FROM metadata)
    ,(SELECT alternative FROM metadata)
    ,(SELECT horizon_year FROM metadata)
    ,'DAILY'
    ,'auto'
    ,'parking_paid'