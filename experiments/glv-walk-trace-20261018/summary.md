| family | r bits | ratio vs rho | theory | productive | in cycles | retries | table+starts+restarts | abandons per 10^4 steps |
|---|---|---|---|---|---|---|---|---|
| j1728 | 24 | 0.944 | 0.707 | 38.6% | 27.0% | 18.2% | 16.2% | 8.4 |
| j1728 | 28 | 0.839 | 0.707 | 47.4% | 22.2% | 17.3% | 13.1% | 8.3 |
| j1728 | 32 | 0.929 | 0.707 | 60.8% | 14.5% | 12.6% | 12.0% | 5.0 |
| j1728 | all | 0.903 | 0.707 | 56.0% | 17.3% | 14.1% | 12.6% | 6.0 |
| j0 | 24 | 0.601 | 0.577 | 50.1% | 13.6% | 14.8% | 21.4% | 5.5 |
| j0 | 28 | 0.547 | 0.577 | 57.8% | 13.0% | 16.1% | 13.1% | 4.8 |
| j0 | 32 | 0.772 | 0.577 | 61.0% | 12.3% | 15.6% | 11.1% | 4.3 |
| j0 | all | 0.633 | 0.577 | 59.7% | 12.5% | 15.7% | 12.1% | 4.5 |
j1728 r=all: abandoned walks in a short cycle 100%; 2-cycles reusing a multiplier after a retry 100%; recover failures 0; lengths {2: 9304, 4: 23565, 5: 1, 6: 2298, 7: 1, 8: 360}
j0 r=all: abandoned walks in a short cycle 100%; 2-cycles reusing a multiplier after a retry 100%; recover failures 0; lengths {2: 7293, 3: 38, 4: 12127, 5: 322, 6: 850, 7: 171}
