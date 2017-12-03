import tensorflow as tf

import data

def main(argv=None):
	next_element = data.get_training_data()

	with tf.Session() as sess:
		print "BEGINNING TRANING..."
		step = 0
		while True:
			try:
			    step += 1
			    print step
			    ex = sess.run([next_element])
			    print ex
			except tf.errors.OutOfRangeError:
			    print("DONE TRAINING")
			    break

if __name__ == "__main__":
	main()