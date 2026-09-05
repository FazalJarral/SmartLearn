# Validation Plan

- SUS target: collect post-task usability surveys and target score >=70.
- Processing success target: measure valid text PDF runs and target >=95%.
- Video success target: measure video jobs excluding provider outages and target >=90%.
- Performance: benchmark extraction plus semantic generation for valid PDFs up to 20 pages and report actual p50/p95. Do not claim the <=10 second target if provider latency prevents it.
- Learning evaluation: compare pre-study and post-study quiz scores on the same concept set, with randomized option order and documented sample size.
- Load: run a 50-concurrent-user script against mock providers before production launch.
