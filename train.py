#!/usr/bin/python3

import os;
import numpy as np;
import tensorflow as tf;
from models import CycleGAN;
from create_dataset import parse_function_generator;

batch_size = 100;
img_shape = (255,255,3);

def main():

  # models
  cycleGAN = CycleGAN();
  optimizer = tf.keras.optimizers.Adam(2e-4);
  # load dataset
  A = tf.data.TFRecordDataset(os.path.join('dataset', 'A.tfrecord')).map(parse_function_generator(img_shape)).shuffle(batch_size).batch(batch_size).__iter__;
  B = tf.data.TFRecordDataset(os.path.join('dataset', 'B.tfrecord')).map(parse_function_generator(img_shape)).shuffle(batch_size).batch(batch_size).__iter__;
  # restore from existing checkpoint
  checkpoint = tf.train.Checkpoint(model = cycleGAN, optimizer = optimizer, optimizer_step = optimizer.iterations);
  checkpoint.restore(tf.train.latest_checkpoint('checkpoints'));
  # create log
  log = tf.summary.create_file_writer('checkpoints');
  # train model
  g_loss = tf.keras.metrics.Mean(name = 'G loss', dtype = tf.float32);
  da_loss = tf.keras.metrics.Mean(name = 'DA loss', dtype = tf.float32);
  db_loss = tf.keras.metrics.Mean(name = 'DB loss', dtype = tf.float32);
  while True:
    imageA, _ = next(A);
    imageB, _ = next(B);
    with tf.GradientTape() as tape:
      outputs = cycleGAN((imageA, imageB));
      G_loss = cycleGAN.G_loss(outputs);    g_loss.update_state(G_loss);
      DA_loss = cycleGAN.DA_loss(outputs);  da_loss.update_state(da_loss);
      DB_loss = cycleGAN.DB_loss(outputs);  db_loss.update_state(db_loss);
    # update generator's parameters
    cycleGAN.set_generator_trainable();
    grads = tape.gradient(G_loss, cycleGAN.trainable_variables);
    optimizer.apply_gradients(zip(grads, cycleGAN.trainable_variables));
    # update discriminator's parameters
    cycleGAN.set_discriminator_trainable();
    grads = tape.gradient(DA_loss, cycleGAN.DA.trainable_variables);
    optimizer.apply_gradients(zip(grads, cycleGAN.DA.trainable_variables));
    grads = tape.gradient(DB_loss, cycleGAN.DB.trainable_variables);
    optimizer.apply_gradients(zip(grads, cycleGAN.DB.trainable_variables));
    # set all parameters trainable
    cycleGAN.set_trainable();
    if tf.equal(optimizer.iterations % 100, 0):
      with log.as_default():
        tf.summary.scalar('generator loss', g_loss.result(), step = optimizer.iterations);
        tf.summary.scalar('discriminator A loss', da_loss.result(), step = optimizer.iterations);
        tf.summary.scalar('discriminator B loss', db_loss.result(), step = optimizer.iterations);
      print('Step #%d G Loss: %.6f DA Loss: %.6f DB Loss: %.6f' % (optimizer.iterations, g_loss.result(), da_loss.result(), db_loss.result()));
      g_loss.reset_states();
      da_loss.reset_states();
      db_loss.reset_states();
    # save model once every epoch
    checkpoint.save(os.path.join('checkpoints', 'ckpt'));
    if G_loss < 0.01 and DA_loss < 0.01 and DB_loss < 0.01: break;
  # save the network structure with weights
  if False == os.path.exists('models'): os.mkdir('models');
  cycleGAN.GA.save(os.path.join('models', 'GA.h5'));
  cycleGAN.GB.save(os.path.join('models', 'GB.h5'));
  cycleGAN.DA.save(os.path.join('models', 'DA.h5'));
  cycleGAN.DB.save(os.path.join('models', 'DB.h5'));

if __name__ == "__main__":
    
  assert True == tf.executing_eagerly();
  main();