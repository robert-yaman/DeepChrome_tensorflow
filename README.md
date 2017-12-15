# Using CNNs to model affect of histone modification on gene expression

WORK IN PROGRESS

Here I implement the CNN described in [DeepChrome: Deep-learning for predicting gene expression from histone modifications](https://academic.oup.com/bioinformatics/article/32/17/i639/2450757) in tensorflow.

This project uses ChIp-Seq data from REMC to identify histone modifications on a set of human epigenomes, and correlates it with RNA-seq gene expression data from the same epigenomes. The goal is to model the effect of the histone modifcations on the expression levels of their respective genes. We do this by constructing 1000 partinions around the TSS of each gene. Each of these partitions has 100 bins of 100 base-pairs each. We then use these partitions as matrices on which to run a convolutional neural network. The convolutions in this network aim to discover long-range structure in the histone modifications. We frame the problem as a binary classifaction problem: either genes have above median expression, or below median expression.

I used toy data [another implementation](https://github.com/QData/DeepChrome) before training on the real dataset.

To generate the data (this takes a long time):

```
python data/get_data.py path/to/data
```

To train the model:
```
python trainer/task.py \
--train-files path/to/training/data
--eval-files path/to/validation/data
--job-dir path/for/model/and/tensorboard
```
This script will use data from the provided paths, and put all output in the job-dir path.
