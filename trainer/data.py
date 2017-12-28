import tensorflow as tf

def get_data(filepath, repeats=1, initializable=False, batch_size=1):
	def decode_line(line):
		items = tf.decode_csv(line, [[0]]*8)
		return items[2:7], items[7]
	def squash_labels(matrix, labels):
		# labels should be a homogenous (100,1) tensor. We turn it into a [2]
		# classification.
		is_ones = tf.reduce_min(labels)
		is_zeros = tf.constant(1) - is_ones
		return matrix, tf.stack([is_ones, is_zeros])
	def rotate_inputs(matrix, labels):
		return tf.transpose(matrix), labels

	base_dataset = tf.contrib.data.TextLineDataset(filepath)
	tr_data = base_dataset.map(decode_line).batch(100).map(
		squash_labels).map(rotate_inputs).batch(batch_size).repeat(repeats)
	if initializable:
		iterator = tr_data.make_initializable_iterator()
	else:
		iterator = tr_data.make_one_shot_iterator()
	next_element = iterator.get_next()

	return next_element, iterator

