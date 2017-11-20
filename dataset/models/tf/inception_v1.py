""" Szegedy C. et al "`Going Deeper with Convolutions
<https://arxiv.org/abs/1409.4842>`_"
"""
import tensorflow as tf

from . import TFModel
from .layers import conv_block


_DEFAULT_V1_ARCH = {
    'arch' : 'bbmbbbbbmbb',
    'layout': 'cn',
    'filters': [
        [64, 96, 128, 16, 32, 32],
        [128, 128, 192, 32, 96, 64],
        [192, 96, 208, 16, 48, 64],
        [160, 112, 224, 24, 64, 64],
        [128, 128, 256, 24, 64, 64],
        [112, 144, 288, 32, 64, 64],
        [256, 160, 320, 32, 128, 128],
        [256, 160, 320, 32, 128, 128],
        [384, 192, 384, 48, 128, 128]
    ],
    'pool_size': 3, 'pool_strides': 2
}


class Inception_v1(TFModel):
    """ Inception network, version 1

    **Configuration**

    inputs : dict
        dict with keys 'images' and 'labels' (see :meth:`._make_inputs`)

    body/arch : dict
        architecture: network layout, block layout, number of filters in each block, pooling parameters
    """
    @classmethod
    def default_config(cls):
        config = TFModel.default_config()
        config['input_block'].update(dict(layout='cnp cn cn p', filters=[64, 64, 192],
                                          kernel_size=[7, 3, 3], strides=[2, 1, 1],
                                          pool_size=3, pool_strides=2))
        config['body']['arch'] = _DEFAULT_V1_ARCH
        config['head'].update(dict(layout='Vdf', dropout_rate=.4))

        return config

    def build_config(self, names=None):
        config = super().build_config(names)
        config['head']['units'] = self.num_classes('targets')
        return config

    @classmethod
    def body(cls, inputs, name='body', **kwargs):
        """ Base layers

        Parameters
        ----------
        inputs : tf.Tensor
            input tensor
        arch : list of dict
            network architecture

        Returns
        -------
        tf.Tensor
        """
        kwargs = cls.fill_params('body', **kwargs)
        filters = kwargs.pop('filters')
        layout = kwargs.pop('layout')

        with tf.variable_scope(name):
            x = inputs
            block_no = 0
            for i, layer in enumerate(kwargs['arch']):
                if layer == 'b':
                    x = cls.block(x, filters[block_no], layout=layout, name='block-%d' % i, **kwargs)
                    block_no += 1
                elif layer == 'p':
                    x = conv_block(x, layout='p', name='max-pooling-%d' % i, **kwargs)
        return x

    @classmethod
    def block(cls, inputs, filters, layout='cn', name=None, **kwargs):
        """ Inception building block

        Parameters
        ----------
        inputs : tf.Tensor
            input tensor
        filters : list with 6 items:
            - number of filters in 1x1 conv
            - number of filters in 1x1 conv going before conv 3x3
            - number of filters in 3x3 conv
            - number of filters in 1x1 conv going before conv 5x5,
            - number of filters in 5x5 conv,
            - number of filters in 1x1 conv going before max-pooling
        layout : str
            a sequence of layers in the block. Default is 'cn'.
        name : str
            scope name

        Returns
        -------
        tf.Tensor
        """
        with tf.variable_scope(name):
            branch_1 = conv_block(inputs, layout, filters[0], 1, name='conv_1', **kwargs)

            branch_3 = conv_block(inputs, layout*2, [filters[1], filters[2]], [1, 3], name='conv_3', **kwargs)

            branch_5 = conv_block(inputs, layout*2, [filters[3], filters[4]], [1, 5], name='conv_5', **kwargs)

            branch_pool = conv_block(inputs, 'p'+layout, filters[5], 1, 'conv_pool', **{**kwargs, 'pool_strides': 1})

            axis = cls.channels_axis(kwargs['data_format'])
            output = tf.concat([branch_1, branch_3, branch_5, branch_pool], axis, name='output')
        return output
