TRAIN_DATA=$(pwd)/toy_data/train.csv
EVAL_DATA=$(pwd)/toy_data/validate.csv
MODEL_DIR=/tmp/deepchrome
rm -rf $MODEL_DIR
gcloud ml-engine local train --module-name trainer.task --package-path trainer/ -- --train-files $TRAIN_DATA --eval-files $EVAL_DATA --job-dir $MODEL_DIR --num-epochs 1 --validation-interval 2 --batch-size 3
