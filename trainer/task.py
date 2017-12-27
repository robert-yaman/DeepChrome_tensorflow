import argparse
import tensorflow as tf

import data
import model

def main(args):
	with tf.device('/gpu:0'):
		next_element, _ = data.get_data(args.train_files, 
			repeats=int(args.num_epochs))
		next_validation_element, val_iterator = data.get_data(args.eval_files, 
			initializable=True)

		x = tf.placeholder(tf.float32, [100,5])
		y = tf.placeholder(tf.float32, [2])
		keep_prob = tf.placeholder(tf.float32)

		readout = model.get_model(x, keep_prob)
		softmax = tf.nn.softmax(readout)

		loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
			labels=y, logits=readout))
		tf.summary.scalar('loss', loss)
		training_step = tf.train.AdamOptimizer(1e-3).minimize(loss)

		unary_prediction = tf.unstack(tf.squeeze(softmax))[0]
		unary_label = tf.unstack(y)[0]
		auc, auc_update = tf.contrib.metrics.streaming_auc(
			predictions=unary_prediction, labels=unary_label, curve='ROC')
		tf.summary.scalar('auc', auc)

	summary = tf.summary.merge_all()
	saver = tf.train.Saver()
	with tf.Session(config=tf.ConfigProto(
      allow_soft_placement=True, log_device_placement=True)) as sess:
		print "BEGINNING TRANING..."
		summary_writer = tf.summary.FileWriter(args.job_dir, sess.graph)

		sess.run(tf.global_variables_initializer())
		sess.run(tf.local_variables_initializer()) 
		step = 0
		while True:
			try:
				step += 1
				print step
				ex, label = sess.run(next_element)
				_, s = sess.run([training_step, summary], 
					feed_dict={x: ex, y: label, keep_prob: 0.5})

				# Validate model
				if step % int(args.validation_interval) == 0:
					# AUC keeps local variables. We reset local variables in 
					# between validation batches.
					sess.run(tf.local_variables_initializer()) 
					sess.run(val_iterator.initializer)
					while True:
						try:
							ex, label = sess.run(next_validation_element)
							sess.run(auc_update, feed_dict={x: ex, y:label, 
								keep_prob: 1})
						except tf.errors.OutOfRangeError:
							print("DONE VALIDATING")
							print "CURRENT AUC:" + str(sess.run(auc))
							break
					print "SAVING CHECKPOINT"
					saver.save(sess, args.job_dir + "/checkpoints/", 
						global_step=step)
				# Log every step for now
				summary_writer.add_summary(s, step)
			except tf.errors.OutOfRangeError:
				print("DONE TRAINING")
				break

if __name__ == "__main__":
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'--train-files',
		help='GCS or local paths to training data',
		nargs='+',
		required=True
	)
	parser.add_argument(
		'--eval-files',
		help='GCS or local paths to evaluation data',
		nargs='+',
		required=True
	)
	parser.add_argument(
		'--job-dir',
		help='GCS location to write checkpoints, tensorboard, and models',
		required=True
	)
	parser.add_argument(
		'--num-epochs',
		default=1,
	)
	parser.add_argument(
		'--validation-interval',
		default=10000
	)

	main(parser.parse_args())
