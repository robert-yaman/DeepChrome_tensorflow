import tensorflow as tf

TRAINING_DATA_FILE = "./toy_data/train.csv"
VALIDATION_DATA_FILE = "./toy_data/validate.csv"
TEST_DATA_FILE = "./toy_data/test.csv"

def get_training_data():
	return _get(TRAINING_DATA_FILE)

def get_validation_data():
	return _get(VALIDATION_DATA_FILE)

def get_test_data():
	return _get(TEST_DATA_FILE)

def _get(filename):
	def decode_line(line):
		items = tf.decode_csv(line, [[0]]*8)
		return items[2:7], items[7]
	def squash_labels(matrix, labels):
		# labels should be a homogenous (100,1) tensor. We turn it into a [2] classification.
		is_ones = tf.reduce_min(labels)
		is_zeros = tf.constant(1) - is_ones
		return matrix, tf.stack([is_ones, is_zeros])

	base_dataset = tf.contrib.data.TextLineDataset(filename)
	tr_data = base_dataset.map(decode_line).batch(100).map(squash_labels)
	iterator = tr_data.make_one_shot_iterator()
	next_element = iterator.get_next()

	return next_element

