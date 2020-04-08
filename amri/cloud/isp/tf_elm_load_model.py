import os

import numpy as np

from amri.cloud.isp.os_elm import OS_ELM
from amri.utils.log_utils import log


def softmax(a):
    c = np.max(a, axis=-1, keepdims=True)
    exp_a = np.exp(a - c)
    sum_exp_a = np.sum(exp_a, axis=-1, keepdims=True)
    return exp_a / sum_exp_a


def main(img):
    noise = 0.03
    img = img.flatten()

    # Normalize
    i_max = 255.0295
    i_min = 2.889e-8
    img = (img - i_min) / (i_max - i_min)
    threshold_indices = np.where(img < 0)[0]
    img[threshold_indices] = 0

    # Threshold
    threshold_ind = np.where(img > noise)[0]
    img = img[threshold_ind]
    img = np.pad(img, (0, 1024 - len(img)), 'constant')
    img = img.reshape(1, 1024)

    # Instantiate os-elm
    n_input_nodes = 1024
    n_hidden_nodes = 1024
    n_output_nodes = 30

    script_path = os.path.abspath(__file__)
    SEARCH_PATH = script_path[:script_path.index('isp') + len('isp') + 1]
    os_elm = OS_ELM(n_input_nodes=n_input_nodes, n_hidden_nodes=n_hidden_nodes, n_output_nodes=n_output_nodes,
                    loss='categorical_crossentropy', activation='sigmoid')

    log('Restoring model parameters...', verbose=False)
    os_elm.restore(SEARCH_PATH + '/checkpoint/model.ckpt')
    x = softmax(os_elm.predict(img)).flatten()
    return np.argmax(x) + 25
