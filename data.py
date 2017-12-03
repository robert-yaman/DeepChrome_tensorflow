import tensorflow as tf

TRAINING_DATA_FILE = "./toy_data/train.csv"

def get_training_data():
	def decode_line(line):
		items = tf.decode_csv(line, [[0]]*8)
		return items[2:7], items[7]
	def squash_labels(matrix, labels):
		# labels should be a homogenous (100,1) tensor.
		return matrix, tf.reduce_min(labels)

	base_dataset = tf.contrib.data.TextLineDataset(TRAINING_DATA_FILE)
	tr_data = base_dataset.map(decode_line).batch(100).map(squash_labels)
	iterator = tr_data.make_one_shot_iterator()
	next_element = iterator.get_next()

	return next_element

