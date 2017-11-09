# pylint: skip-file
import os
import sys
from time import time
import numpy as np
import tensorflow as tf

sys.path.append("../..")
from dataset import Pipeline, B, C, F, V, action, ImagesBatch
from dataset.opensets import MNIST
from dataset.models.tf import TFModel
from dataset.models.tf.layers import conv_block


class MyModel(TFModel):
    def _build(self):
        names = ['images', 'labels']
        placeholders, inputs = self._make_inputs(names)

        num_classes = self.num_classes('labels')
        dim = 2
        x = inputs['images']
        x = conv_block(dim, x, [16, 32, 64], 3, strides=[1, 2, 2], dropout_rate=.15,
                         layout='cna cna cna', depth_multiplier=[1, 2, 2],
                         name='network', training=self.is_training)
        x = self.head(dim, x, 'conv', num_classes=num_classes, training=self.is_training)
        x = tf.identity(x, name='predictions')

        predicted_labels = self.to_classes(x, 'labels', name='predicted_labels')

class MyBatch(ImagesBatch):
    components = 'images', 'labels', 'digits'
    @action
    def make_digits(self):
        self.digits = (10 + self.labels).astype('str')
        return self


if __name__ == "__main__":
    BATCH_SIZE = 64

    mnist = MNIST(batch_class=MyBatch)
    config = dict(some=1, conv=dict(arg1=10))
    print()
    print("Start training...")
    t = time()
    train_tp = (Pipeline(config=config)
                .init_variable('loss_history', init_on_each_run=list)
                .init_variable('current_loss', init_on_each_run=0)
                .init_variable('pred_label', init_on_each_run=list)
                .init_variable('input_tensor_name', 'images')
                .init_model('dynamic', MyModel, 'conv',
                            config={'session': {'config': tf.ConfigProto(allow_soft_placement=True)},
                                    'loss': 'ce',
                                    'optimizer': {'name':'Adam', 'use_locking': True},
                                    'inputs': dict(images={'shape': (28, 28, 1), 'transform': 'mip @ 1'},
                                                   #labels={'shape': 10, 'dtype': 'uint8',
                                                   labels={'classes': (10+np.arange(10)).astype('str'),
                                                           'transform': 'ohe', 'name': 'targets'})})
                .make_digits()
                .train_model('conv', fetches=['loss', 'predicted_labels'],
                                     feed_dict={V('input_tensor_name'): B('images'),
                                                'labels': B('digits')},
                             save_to=[V('current_loss'), V('pred_label')])
                .print_variable('current_loss')
                .update_variable('loss_history', V('current_loss'), mode='a'))

    train_pp = (train_tp << mnist.train)
    train_pp.run(BATCH_SIZE, shuffle=True, n_epochs=1, drop_last=True, prefetch=0)
    print("End training", time() - t)


    print()
    print("Start testing...")
    t = time()
    test_pp = (mnist.test.p
                .import_model('conv', train_pp)
                .init_variable('all_targets', init_on_each_run=list)
                .init_variable('all_predictions', init_on_each_run=list)
                .make_digits()
                .predict_model('conv', fetches='predicted_labels', feed_dict={'images': B('images'),
                                                                              'labels': B('digits')},
                               save_to=V('all_predictions'), mode='a')
                .update_variable('all_targets', B('digits'), mode='a')
                .run(BATCH_SIZE, shuffle=True, n_epochs=1, drop_last=False, prefetch=0))
    print("End testing", time() - t)

    print("Predictions")
    predictions = np.concatenate(test_pp.get_variable('all_predictions'))
    targets = np.concatenate(test_pp.get_variable('all_targets'))
    accuracy = (predictions == targets).sum() / len(predictions) * 100
    print('Accuracy {:6.2f}'.format(accuracy))
    print(targets)
    print(predictions)


    conv = train_pp.get_model_by_name("conv")
