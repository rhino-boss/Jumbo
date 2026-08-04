-- Materializes the reviewed output of cascade_distribution_analysis.py.
-- SQLite-compatible; rates are fractions and diff_pp is percentage points.
WITH comparison(scene, bin, sort_order, h028_count, h028_rate, lucky_count, lucky_rate, diff_pp) AS (
    VALUES
        ('BG', '0 次', 0, 643890, 0.6438900000, 34101, 0.7239051521, -8.0015),
        ('BG', '1 次', 1, 146702, 0.1467020000,  9076, 0.1926677564, -4.5966),
        ('BG', '2 次', 2,  85108, 0.0851080000,  2206, 0.0468295582,  3.8278),
        ('BG', '3 次', 3,  54029, 0.0540290000,   932, 0.0197847454,  3.4244),
        ('BG', '4 次', 4,  33334, 0.0333340000,   406, 0.0086186766,  2.4715),
        ('BG', '5+ 次', 5, 36937, 0.0369370000,   386, 0.0081941113,  2.8743),
        ('FG', '0 次', 0,  30776, 0.5805258988,   965, 0.6352863726, -5.4760),
        ('FG', '1 次', 1,   9999, 0.1886105557,   326, 0.2146148782, -2.6004),
        ('FG', '2 次', 2,   5301, 0.0999924548,   110, 0.0724160632,  2.7576),
        ('FG', '3 次', 3,   3135, 0.0591353227,    68, 0.0447662936,  1.4369),
        ('FG', '4 次', 4,   1820, 0.0343305542,    28, 0.0184331797,  1.5897),
        ('FG', '5+ 次', 5,  1983, 0.0374052137,    22, 0.0144832126,  2.2922)
)
SELECT scene, bin, sort_order, h028_count, h028_rate, lucky_count, lucky_rate, diff_pp
FROM comparison
ORDER BY CASE scene WHEN 'BG' THEN 0 ELSE 1 END, sort_order;
