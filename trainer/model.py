import tensorflow as tf
import math

EXAMPLE_WIDTH = 100
NUM_CONV_FILTERS = 50
CONV_FILTER_SIZE = 10
POOLING_SIZE = 5
FIRST_FC_LAYER_NODE_COUNT = 625
SECOND_FC_LAYER_NODE_COUNT = 125

def _variable_summaries(var):
    """Attach a lot of summaries to a Tensor (for TensorBoard
    visualization)."""
    with tf.name_scope('summaries'):
        mean = tf.reduce_mean(var)
        tf.summary.scalar('mean', mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.summary.scalar('stddev', stddev)
        tf.summary.scalar('max', tf.reduce_max(var))
        tf.summary.scalar('min',tf.reduce_min(var))
        tf.summary.histogram('histogram',var)

def get_model(x, keep_prob):
	def weight_variables(shape, name="weights"):
		with tf.name_scope('weights'):
			variables = tf.get_variable(name, shape, 
				initializer=tf.truncated_normal_initializer(stddev=.1))
			_variable_summaries(variables)
			return variables
	def bias_variables(shape):
		with tf.name_scope('biases'):
			variables = tf.get_variable("biases", shape, 
				initializer=tf.constant_initializer(0.1))
			_variable_summaries(variables)
			return variables

	with tf.name_scope('initialize'):
	    # Add a |channel| dimension for convolution.
	    ## TODO: double check tf.transpose is what we want.
		example_4d = tf.expand_dims(x, [-1])

	with tf.variable_scope('conv'):
		# NOTE: don't need to take into account batch size here.
		conv_weights = weight_variables([5, CONV_FILTER_SIZE, 1, NUM_CONV_FILTERS])
		conv_biases = bias_variables([NUM_CONV_FILTERS])

		conv = tf.nn.conv2d(example_4d, conv_weights, 
			strides=[1,1,1,1] ,padding='VALID')
		conv_relu = tf.nn.relu(conv + conv_biases)
		pool = tf.nn.pool(conv_relu, window_shape=[1,POOLING_SIZE], 
			pooling_type='MAX', padding='VALID', strides=[1,POOLING_SIZE])

	with tf.variable_scope('dropout'):
		total_nodes = ((EXAMPLE_WIDTH - CONV_FILTER_SIZE) / POOLING_SIZE) * NUM_CONV_FILTERS
		pool_flat = tf.reshape(pool, [-1, total_nodes])

		dropout_layer = tf.nn.dropout(pool_flat, keep_prob)

	with tf.variable_scope('first_fc_layer'):
		first_fc_weights = weight_variables([total_nodes, 
			FIRST_FC_LAYER_NODE_COUNT])
		first_fc_biases = bias_variables([FIRST_FC_LAYER_NODE_COUNT])
		first_fc_layer = tf.nn.relu(tf.matmul(dropout_layer, first_fc_weights) + first_fc_biases)

	with tf.variable_scope('second_fc_layer'):
		second_fc_weights = weight_variables([FIRST_FC_LAYER_NODE_COUNT,
			SECOND_FC_LAYER_NODE_COUNT])
		second_fc_biases = bias_variables([SECOND_FC_LAYER_NODE_COUNT])
		second_fc_layer = tf.nn.relu(tf.matmul(first_fc_layer, second_fc_weights) + second_fc_biases)

	with tf.variable_scope('readout'):
		# 2 outputs (mutually exclusive classification).
		readout_weights = weight_variables([SECOND_FC_LAYER_NODE_COUNT, 2])
		readout_biases = bias_variables([2])
		readout = tf.matmul(second_fc_layer, readout_weights) + readout_biases

	return readout
