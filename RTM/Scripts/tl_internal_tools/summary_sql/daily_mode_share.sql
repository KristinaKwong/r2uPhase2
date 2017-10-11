SELECT

    (SELECT scenario FROM metadata) as scenario
    ,(SELECT alternative FROM metadata) as alternative
    ,(SELECT horizon_year FROM metadata) as horizon_year
    ,'DAILY' as peak
    ,LOWER(mode) as mode
    ,'mode_share' as measure
    ,share as value

FROM vModeShareDaily