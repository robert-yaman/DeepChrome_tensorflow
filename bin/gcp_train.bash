gcloud config set project deepchrome-188918
cd /Users/robertyaman/DeepChrome
BUCKET_NAME=deepchrome-data
REGION=us-central1
DATE=$(date +"%m%d%y%s")
JOB_NAME="deepchrome_train$DATE"
TRAIN_DATA=gs://$BUCKET_NAME/data/training_data.csv
EVAL_DATA=gs://$BUCKET_NAME/data/validation_data.csv
OUTPUT_PATH=gs://$BUCKET_NAME/$JOB_NAME
gcloud ml-engine jobs submit training $JOB_NAME \
--job-dir $OUTPUT_PATH \
--runtime-version 1.4 \
--module-name trainer.task \
--package-path trainer/ \
--region $REGION \
-- \
--train-files $TRAIN_DATA \
--eval-files $EVAL_DATA \
--num-epochs 5 \
--batch-size 256