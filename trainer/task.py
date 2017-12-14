import argparse
import tensorflow as tf

import data
import model

def main(args):
	next_element = data.get_data(args.train_files)
	next_validation_element = data.get_data(args.eval_files)

	x = tf.placeholder(tf.float32, [100,5])
	y = tf.placeholder(tf.float32)
	keep_prob = tf.placeholder(tf.float32)

	readout = model.get_model(x, keep_prob)
	softmax = tf.nn.softmax(readout)

	loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y, 
		logits=readout))
	tf.summary.scalar('loss', loss)
	# Try Adam optimizer?
	training_step = tf.train.GradientDescentOptimizer(1e-3).minimize(loss)

	# This seems wrong - we are analyzing as if both labels could be true.
	auc, auc_update = tf.contrib.metrics.streaming_auc(predictions=softmax, 
		labels=y, curve='ROC')

	summary = tf.summary.merge_all()
	with tf.Session() as sess:
		print "BEGINNING TRANING..."
		summary_writer = tf.summary.FileWriter(args.job_dir, sess.graph)

		sess.run(tf.global_variables_initializer())
		step = 0
		while True:
			try:
			    step += 1
			    print step
			    ex, label = sess.run(next_element)
			    _, s = sess.run([training_step, summary], 
			    	feed_dict={x: ex, y: label, keep_prob: 0.5})
			    # Log every step for now
			    summary_writer.add_summary(s, step)
			except tf.errors.OutOfRangeError:
			    print("DONE TRAINING")
			    break

		# Validate model
		sess.run(tf.local_variables_initializer()) # AUC keeps local variables

		while True:
			try:
				ex, label = sess.run(next_validation_element)
				sess.run(auc_update, feed_dict={x: ex, y:label, keep_prob: 1})
			except tf.errors.OutOfRangeError:
				print("DONE VALIDATING")
				break

		ending_auc = sess.run(auc)
		print "AUC:"
		print ending_auc

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	# Input Arguments
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

	main(parser.parse_args())
