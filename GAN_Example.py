# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 20:34:19 2019

@author: wangjingyi
"""

# GAN Paper https://arxiv.org/pdf/1406.2661.pdf
import os
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

# 以minst数据集为例
mnist = input_data.read_data_sets("MNIST_data", one_hot=True)

num_steps = 100000
batch_size = 128
learning_rate = 0.0002
image_dim = 784
model_path = "./save/model.ckpt"

gen_hidden_dim = 256
disc_hidden_dim = 256
noise_dim = 100


# Xavier初始化,注意权重都是Xavier初始化生成的
def xavier_glorot_init(shape):
   # 正态分布中取随机值
   # stddev=1. / tf.sqrt(shape[0] / 2.)保证每一层方差一致
   return tf.random_normal(shape=shape, stddev=1. / tf.sqrt(shape[0] / 2.))


# G是一个生成图片的网络,它接收一个随机的噪声z,通过这个噪声生成图片,记做G(z)
# D是一个判别网络,判别一张图片是不是"真实的",它的输入参数是x,x代表一张图片,输出D(x)代表x为真实图片的概率
# 如果为1,就代表100%是真实的图片,而输出为0,就代表不可能是真实的图片

# 权重w和b设置
weights = {
   "gen_hidden1": tf.Variable(xavier_glorot_init([noise_dim, gen_hidden_dim])),
   "gen_out": tf.Variable(xavier_glorot_init([gen_hidden_dim, image_dim])),
   "disc_hidden1": tf.Variable(xavier_glorot_init([image_dim, disc_hidden_dim])),
   "disc_out": tf.Variable(xavier_glorot_init([disc_hidden_dim, 1])),
}

biases = {
   "gen_hidden1": tf.Variable(tf.zeros([gen_hidden_dim])),
   "gen_out": tf.Variable(tf.zeros([image_dim])),
   "disc_hidden1": tf.Variable(tf.zeros([disc_hidden_dim])),
   "disc_out": tf.Variable(tf.zeros([1])),
}


# G是一个生成图片的网络,它接收一个随机的噪声z,通过这个噪声最终生成图片,记做G(z)
def generator(x):
   # 隐藏层y=wx+b,然后经过激活函数relu处理
   hidden_layer = tf.nn.relu(tf.add(tf.matmul(x, weights["gen_hidden1"]), biases["gen_hidden1"]))
   # 输出层y=wx+b,然后经过sigmoid函数处理
   out_layer = tf.nn.sigmoid(tf.add(tf.matmul(hidden_layer, weights["gen_out"]), biases["gen_out"]))

   return out_layer


# D是一个判别网络,判别一张图片是不是"真实的",它的输入参数是x,x代表一张图片,输出D(x)代表x为真实图片的概率
# 如果为1,就代表100%是真实的图片,而输出为0,就代表不可能是真实的图片
def discriminator(x):
   # 隐藏层y=wx+b,然后经过激活函数relu处理
   hidden_layer = tf.nn.relu(tf.add(tf.matmul(x, weights["disc_hidden1"]), biases["disc_hidden1"]))
   # 输出层y=wx+b,然后经过sigmoid函数处理
   out_layer = tf.nn.sigmoid(tf.add(tf.matmul(hidden_layer, weights["disc_out"]), biases["disc_out"]))

   return out_layer


# G和D的输入placeholder变量
gen_input = tf.placeholder(tf.float32, shape=[None, noise_dim], name="input_noise")
disc_input = tf.placeholder(tf.float32, shape=[None, image_dim], name="disc_input")
# 建立G网络
gen_sample = generator(gen_input)
# 建立两个D网络,一个以真实数据输入,一个以G网络的输出作输入
disc_real = discriminator(disc_input)
disc_fake = discriminator(gen_sample)

# 定义两个损失函数,G网络的损失函数是生成的样本的D网络输出的对数损失函数,D网络的损失函数是交叉熵损失函数
gen_loss = -tf.reduce_mean(tf.log(disc_fake))
disc_loss = -tf.reduce_mean(tf.log(disc_real) + tf.log(1. - disc_fake))

# G网络和D网络的变量
gen_vars = [weights["gen_hidden1"], weights["gen_out"], biases["gen_hidden1"], biases["gen_out"]]
disc_vars = [weights["disc_hidden1"], weights["disc_out"], biases["disc_hidden1"], biases["disc_out"]]

# G网络和D网路都使用Adam算法优化
train_gen = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(gen_loss, var_list=gen_vars)
train_disc = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(disc_loss, var_list=disc_vars)

if not os.path.exists("./save/"):
   os.mkdir("./save/")
# 定义saver对象,用来保存/恢复模型
saver = tf.train.Saver(max_to_keep=5)

# 训练G和D网络
with tf.Session() as sess:
   sess.run(tf.global_variables_initializer())
   # 恢复模型
   if os.path.exists("./save/checkpoint"):
      # 判断最新的保存模型检查点是否存在，如果存在则从最近的检查点恢复模型
      saver.restore(sess, tf.train.latest_checkpoint("./save/"))
   for i in range(num_steps):
      # 只用图片数据进行训练
      batch_x, _ = mnist.train.next_batch(batch_size)
      # 生成噪声,数值从-1到1的均匀分布中随机取值
      z_input = np.random.uniform(-1., 1., size=[batch_size, noise_dim])
      # D网络输入即真实图片,G网络输入为生成的噪声,它们的数量都是batch_size
      feed_dict = {disc_input: batch_x, gen_input: z_input}
      _, _, g_loss, d_loss = sess.run([train_gen, train_disc, gen_loss, disc_loss], feed_dict=feed_dict)
      if i % 1000 == 0:
         print("Step:{} Generator Loss:{:.4f} Discriminator Loss:{:.4f}".format(i, g_loss, d_loss))
         save_path = saver.save(sess, model_path, global_step=i)
         print("模型保存到文件夹:{}".format(save_path))
         if g_loss <= 3 and d_loss <= 0.4:
            break

   f, a = plt.subplots(4, 10, figsize=(10, 4))
   # 生成4张x10轮图片,共40张图片
   for i in range(10):
      # 随机生成噪声,噪声也是均匀分布中随机取值,用训练好的G网络生成图片
      z_input = np.random.uniform(-1., 1., size=[4, noise_dim])
      g_sample = sess.run([gen_sample], feed_dict={gen_input: z_input})
      g_sample = np.reshape(g_sample, newshape=(4, 28, 28, 1))
      # 使用反差色可以更好地显示图片,g_sample中每个像素点上都是[0,1]内的值
      g_sample = -1 * (g_sample - 1)
      # 把40张图片画出来
      for j in range(4):
         # 每个像素点在2号维度扩展成3个值,3个值都是原来的第一个值
         img = np.reshape(np.repeat(g_sample[j][:, :, np.newaxis], 3, axis=2), newshape=(28, 28, 3))
         # 画出每张子图
         a[j][i].imshow(img)

   f.show()
   plt.draw()
   plt.waitforbuttonpress()

