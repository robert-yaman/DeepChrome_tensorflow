# The Data

Each row represents one base pair.

We separate the data into bins of 100 base pairs to run convolutions.

* Column 0: (?)
* Column 1: the row of the bin
* Columns 2-6: the histone modifications
* Column 7: the label - 1 if this region has higher than median expression, else 0. 