import numpy as np
import tqdm
from keras.utils import to_categorical

from amri.cloud.isp.os_elm import OS_ELM


def main():
    # Instantiate os-elm
    n_input_nodes = 1024
    n_hidden_nodes = 1024
    n_output_nodes = 30

    os_elm = OS_ELM(n_input_nodes=n_input_nodes,  # the number of input nodes
                    n_hidden_nodes=n_hidden_nodes,  # the number of hidden nodes
                    n_output_nodes=n_output_nodes,  # the number of output nodes
                    # loss function; 'mean_absolute_error', 'categorical_crossentropy', and 'binary_crossentropy'.
                    loss='categorical_crossentropy', activation='sigmoid')

    # Prepare dataset
    n_classes = n_output_nodes

    x = np.load('/Users/sravan953/gpi/sravan953/imr-framework/do_not_publish/isp_datagen/dataset_x.npy')
    y = np.load('/Users/sravan953/gpi/sravan953/imr-framework/do_not_publish/isp_datagen/dataset_y.npy')

    # Shuffle
    shuffle_limit = x.shape[0]
    train_limit = round(0.9 * shuffle_limit)
    print('Total {}, train {}'.format(shuffle_limit, train_limit))
    shuffle_indices = np.random.randint(0, shuffle_limit, shuffle_limit)
    x_train = x[shuffle_indices[:train_limit]]
    x_test = x[shuffle_indices[train_limit:]]

    # convert label data into one-hot-vector format data.
    t_train = to_categorical(y[shuffle_indices[:train_limit]], n_classes)
    t_test = to_categorical(y[shuffle_indices[train_limit:]], n_classes)

    # NOTE: the number of training samples for the initial training phase
    # must be much greater than the number of the model's hidden nodes.
    # here, we assign int(1.5 * n_hidden_nodes) training samples
    # for the initial training phase.
    border = int(1.5 * n_hidden_nodes)
    x_train_init = x_train[:border]
    x_train_seq = x_train[border:]
    t_train_init = t_train[:border]
    t_train_seq = t_train[border:]

    # Training
    # The initial training phase
    pbar = tqdm.tqdm(total=len(x_train), desc='initial training phase')
    os_elm.init_train(x_train_init, t_train_init)
    pbar.update(n=len(x_train_init))

    # the sequential training phase
    pbar.set_description('sequential training phase')
    batch_size = 64
    for i in range(0, len(x_train_seq), batch_size):
        x_batch = x_train_seq[i:i + batch_size]
        t_batch = t_train_seq[i:i + batch_size]
        os_elm.seq_train(x_batch, t_batch)
        pbar.update(n=len(x_batch))
    pbar.close()

    # Evaluation
    [loss, accuracy] = os_elm.evaluate(x_test, t_test, metrics=['loss', 'accuracy'])
    print('val_loss: , val_accuracy: {}'.format(accuracy))

    # Save model
    if accuracy * 100 > 75:
        os_elm.save(
            './checkpoint/val_acc_{folder:0.3g}/model.ckpt'.format(folder=accuracy * 100))


if __name__ == '__main__':
    NUM_RUNS = 10
    for i in range(NUM_RUNS):
        print('Run {} '.format(i), end='')
        main()
