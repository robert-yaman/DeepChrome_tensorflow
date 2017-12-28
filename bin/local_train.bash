# TRAIN_DATA=$(pwd)/toy_data/train.csv
# EVAL_DATA=$(pwd)/toy_data/validate.csv
TRAIN_DATA=gs://deepchrome-data/data/training_data.csv
EVAL_DATA=gs://deepchrome-data/data/validation_data.csv
MODEL_DIR=/tmp/deepchrome
rm -rf $MODEL_DIR
gcloud ml-engine local train --module-name trainer.task --package-path trainer/ -- --train-files $TRAIN_DATA --eval-files $EVAL_DATA --job-dir $MODEL_DIR --num-epochs 1 --validation-interval 2
