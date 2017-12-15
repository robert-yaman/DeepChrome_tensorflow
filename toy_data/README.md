# The Data

Each row represents a bin of one hundred base pairs.

We separate the data into partitions of 100 examples (1000 base pairs total) to run  convolutions.

* Column 0: Example number
* Column 1: the row of the partition
* Columns 2-6: the histone modifications
	* H3K4me3
	* H3K4me1
	* H3K36me3
	* H3K9me3
	* H3K27me3
* Column 7: the label - 1 if this region has higher than median expression, else 0