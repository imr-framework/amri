import numpy as np
import pandas as pd

from amri.utils import constants
from amri.utils.log_utils import log
from amri.utils.make_t1_mprage import make_t1_mprage
from amri.utils.make_t2_se import make_t2_se
from amri.utils.make_t2_star_gre import make_t2_star_se


class LUT:
    def __init__(self):
        pd.set_option('display.max_columns', None)
        self.t1_dataframe, self.t2_dataframe, self.t2_star_dataframe = None, None, None

        self.t1_acq = 0
        self.t2_acq = 0
        self.t2_star_acq = 0

        self.snr_threshold = 9
        self.snr_threshold_db = 20 * np.log10(self.snr_threshold)  # 20log10(snr)

    def __make_lut(self, nsa_multiplier=(1, 1, 1), time_acq_multiplier=(1, 1, 1)):  # time_acq_multiplier???
        num_values = 10  # number of values in linspace
        num_slices = 3

        self.__make_t1_dataframe(num_values=num_values, num_slices=num_slices, nsa_multiplier=nsa_multiplier[0],
                                 time_acq_multiplier=time_acq_multiplier[0])
        self.__make_t2_dataframe(num_values=num_values, num_slices=num_slices, nsa_multiplier=nsa_multiplier[1],
                                 time_acq_multiplier=time_acq_multiplier[1])
        self.__make_t2_star_dataframe(num_values=num_values, num_slices=num_slices, nsa_multiplier=nsa_multiplier[2],
                                      time_acq_multiplier=time_acq_multiplier[2])

    def __make_t1_dataframe(self, num_values, num_slices, nsa_multiplier=1, time_acq_multiplier=1):
        t1w_signal, t1g_signal, t1c_signal = [], [], []
        t_acq_arr = []
        te = 6.5e-3
        ti = 140e-3
        tr = 13e-3
        flip = 12
        t1w_signal.append(self.get_signal_intensity(te, tr, flip, 'white') * nsa_multiplier)
        t1g_signal.append(self.get_signal_intensity(te, tr, flip, 'gray') * nsa_multiplier)
        t1c_signal.append(self.get_signal_intensity(te, tr, flip, 'csf') * nsa_multiplier)
        t_acq_arr.append(128 * (ti + tr) * num_slices * time_acq_multiplier)  # Ny = 128
        t1_dataframe = pd.DataFrame({'TR (s)': tr,
                                     'tau (s)': te,
                                     'FA (deg)': flip,
                                     'T acq (s)': t_acq_arr,
                                     'Sw': t1w_signal,
                                     'Sg': t1g_signal,
                                     'Sc': t1c_signal})
        t1_dataframe['Cwg'] = t1_dataframe['Sw'] - t1_dataframe['Sg']
        self.t1_dataframe = t1_dataframe.sort_values(by='Cwg', ascending=False)

    def __make_t2_dataframe(self, num_values, num_slices, nsa_multiplier=1, time_acq_multiplier=1):
        t2w_signal, t2g_signal, t2c_signal = [], [], []
        t_acq_arr = []
        te_arr = []
        tr_arr = []
        flip = 90

        for te in np.linspace(100e-3, 350e-3, num_values):
            for tr in np.linspace(1500e-3, 3000e-3, num_values):
                te_arr.append(te)
                tr_arr.append(tr)
                t2w_signal.append(self.get_signal_intensity(te, tr, flip, 'white') * nsa_multiplier)
                t2g_signal.append(self.get_signal_intensity(te, tr, flip, 'gray') * nsa_multiplier)
                t2c_signal.append(self.get_signal_intensity(te, tr, flip, 'csf') * nsa_multiplier)
                t_acq_arr.append(128 * tr * num_slices * time_acq_multiplier)  # Ny = 128
        t2_dataframe = pd.DataFrame({'TR (s)': tr_arr,
                                     'tau (s)': te_arr,
                                     'FA (deg)': flip,
                                     'T acq (s)': t_acq_arr,
                                     'Sw': t2w_signal,
                                     'Sg': t2g_signal,
                                     'Sc': t2c_signal})
        t2_dataframe['Cwg'] = t2_dataframe['Sg'] - t2_dataframe['Sw']
        self.t2_dataframe = t2_dataframe.sort_values(by='Cwg', ascending=False)

    def __make_t2_star_dataframe(self, num_values, num_slices, nsa_multiplier=1, time_acq_multiplier=1):
        t2_starw_signal, t2_starg_signal, t2_starc_signal = [], [], []
        t_acq_arr = []
        te_arr = []
        tr_arr = []
        flip_arr = []

        for te in np.linspace(20e-3, 50e-3, num_values):
            for tr in np.linspace(100e-3, 300e-3, num_values):
                for flip in np.linspace(5, 20, num_values):
                    te_arr.append(te)
                    tr_arr.append(tr)
                    flip_arr.append(flip)
                    t2_starw_signal.append(self.get_signal_intensity(te, tr, flip, 'white') * nsa_multiplier)
                    t2_starg_signal.append(self.get_signal_intensity(te, tr, flip, 'gray') * nsa_multiplier)
                    t2_starc_signal.append(self.get_signal_intensity(te, tr, flip, 'csf') * nsa_multiplier)
                    t_acq_arr.append(128 * tr * num_slices * time_acq_multiplier)  # Ny = 128
        t2_star_dataframe = pd.DataFrame({'TR (s)': tr_arr,
                                          'tau (s)': te_arr,
                                          'FA (deg)': flip_arr,
                                          'T acq (s)': t_acq_arr,
                                          'Sw': t2_starw_signal,
                                          'Sg': t2_starg_signal,
                                          'Sc': t2_starc_signal})
        t2_star_dataframe['Cwg'] = t2_star_dataframe['Sc'] - t2_star_dataframe['Sg']
        self.t2_star_dataframe = t2_star_dataframe.sort_values(by='Cwg', ascending=False)

    def get_signal_intensity(self, te, tr, flip, matter):
        # Contrast signal intensities across gray, white and CSF matters respectively
        t1_signal = [1.331, 0.832, 4.163]
        pd_signal = [0.82, 0.7, 1]
        t2_signal = [0.011, 0.08, 2]
        t2_star_signal = [0.110, 0.080, 1.800]

        flip = np.multiply(flip, np.pi / 180)
        # im is for selecting matter
        im = 0 if matter == 'gray' else -1
        im = 1 if matter == 'white' else im
        im = 2 if matter == 'csf' else im

        e1 = np.exp(-tr / t1_signal[im])
        e2 = np.exp(-te / t2_star_signal[im])
        S1 = pd_signal[im] * np.sin(flip) * (1 - e1) * e2
        S2 = 1 - np.multiply(np.cos(flip), e1)
        S = np.divide(S1, S2)
        return S

    def _get_parameters_from_dataframe(self, id, verbose=True):
        dataframe = getattr(self, id + '_dataframe')  # id is t1/t2/t2_star

        while True:  # Check if best contrast has acceptable SNR
            signal_max = dataframe.loc[:, ['Sw', 'Sg', 'Sc']].iloc[0]
            signal_max = signal_max.max()
            if 20 * np.log10(signal_max / self.noise_acq) >= self.snr_threshold_db:
                break
            dataframe = dataframe.drop(dataframe.index[0])  # Set value to dataframe that was passed

        te = dataframe['tau (s)'].iloc[0]
        tr = dataframe['TR (s)'].iloc[0]
        flip = dataframe['FA (deg)'].iloc[0]
        t_acq = dataframe['T acq (s)'].iloc[0]  # Set value to t_acq that was passed

        setattr(self, id + '_dataframe', dataframe)
        setattr(self, id + '_acq', t_acq)

        log('te={:.3g}s tr={:.3g}s flip={:.3g} acq_time={:.3g}s'.format(te, tr, flip, t_acq), verbose=verbose)
        return [round(te, 4), round(tr, 4), round(flip, 3), t_acq], signal_max

    def get_last_n_sequences(self, time_seconds_remaining, last_n):
        self.__make_lut()
        penalize_counter = 0

        while True:
            try:
                all_snrs = []
                if last_n == 3:
                    t1_params, best_signal_max = self._get_parameters_from_dataframe(id='t1', verbose=False)
                    all_snrs.append(round(20 * np.log10(best_signal_max / self.noise_acq), 3))
                    t2_params, _ = self._get_parameters_from_dataframe(id='t2', verbose=False)
                    all_snrs.append(round(20 * np.log10(_ / self.noise_acq), 3))
                    t2_star_params, _ = self._get_parameters_from_dataframe(id='t2_star', verbose=False)
                    all_snrs.append(round(20 * np.log10(_ / self.noise_acq), 3))
                elif last_n == 2:
                    t2_params, best_signal_max = self._get_parameters_from_dataframe(id='t2', verbose=False)
                    all_snrs.append(round(20 * np.log10(best_signal_max / self.noise_acq), 3))
                    t2_star_params, _ = self._get_parameters_from_dataframe(id='t2_star', verbose=False)
                    all_snrs.append(round(20 * np.log10(_ / self.noise_acq), 3))
                elif last_n == 1:
                    t2_star_params, best_signal_max = self._get_parameters_from_dataframe(id='t2_star', verbose=False)
                    all_snrs.append(round(20 * np.log10(best_signal_max / self.noise_acq), 3))
            except IndexError:
                time_seconds_remaining += 15
                self.__make_lut()
                penalize_counter = 0

                log('Increasing time to spend to {}, '.format(time_seconds_remaining), endline='')
                log('SNR(s): {}dB vs {}dB, '.format(all_snrs, round(self.snr_threshold_db, 3)), endline='')
                log('repopulating LUT...')
                continue

            if penalize_counter == 0:
                if 't1_params' in locals():
                    best_t1_params = t1_params
                if 't2_params' in locals():
                    best_t2_params = t2_params
                if 't2_star_params' in locals():
                    best_t2_star_params = t2_star_params

            t_acq_sigma = self.t1_acq + self.t2_acq + self.t2_star_acq
            if t_acq_sigma <= time_seconds_remaining:
                break

            try:
                if penalize_counter % 2 == 0:
                    self.t2_dataframe = self.t2_dataframe.drop(self.t2_dataframe.index[0])
                else:
                    self.t2_star_dataframe = self.t2_star_dataframe.drop(self.t2_star_dataframe.index[0])
            except:
                time_seconds_remaining += 15
                self.__make_lut()
                penalize_counter = 0

                log('Increasing time to spend to {}, '.format(time_seconds_remaining), endline='')
                log('repopulating LUT...')
                continue
            penalize_counter += 1

        log("=========")
        log('Noise from previous acquisition: {:.3g}'.format(self.noise_acq))
        log('Contrast & SNR (={}dB > {}dB) optimized parameters:'.format(all_snrs, round(self.snr_threshold_db, 3)))
        if 't1_params' in locals():
            log('T1w: te={:.3g}s tr={:.3g}s flip={:.3g} acq_time={:.3g}s'.format(*best_t1_params))
        if 't2_params' in locals():
            log('T2w: te={:.3g}s tr={:.3g}s flip={:.3g} acq_time={:.3g}s'.format(*best_t2_params))
        if 't2_star_params' in locals():
            log('T2*w: te={:.3g}s tr={:.3g}s flip={:.3g} acq_time={:.3g}s'.format(*best_t2_star_params))

        t = time_seconds_remaining
        if last_n == 3:
            t -= self.t1_acq
            t1_seq = make_t1_mprage(*t1_params[:-1])
            t2_seq = make_t2_se(*t2_params[:-1])
            t2_star_seq = make_t2_star_se(*t2_star_params[:-1])
            seq = t1_seq
        elif last_n == 2:
            t -= (self.t1_acq + self.t2_acq)
            t2_seq = make_t2_se(*t2_params[:-1])
            t2_star_seq = make_t2_star_se(*t2_star_params[:-1])
            seq = t2_seq
        elif last_n == 1:
            t -= (self.t1_acq + self.t2_acq + self.t2_star_acq)
            t2_star_seq = make_t2_star_se(*t2_star_params[:-1])
            seq = t2_star_seq

        log('\nTime (remaining={:1g}s) optimized parameters:'.format(t))
        if 't1_params' in locals():
            log('T1w: te={:.3g}s tr={:.3g}s flip={:.3g} acq_time={:.3g}s'.format(*t1_params))
        if 't2_params' in locals():
            log('T2w: te={:.3g}s tr={:.3g}s flip={:.3g} acq_time={:.3g}s'.format(*t2_params))
        if 't2_star_params' in locals():
            log('T2*w: te={:.3g}s tr={:.3g}s flip={:.3g} acq_time={:.3g}s'.format(*t2_star_params))

        return seq, time_seconds_remaining

    def update_lut_from_image(self, image, patch_size=10):
        image_min = np.amin(image)
        image_max = np.amax(image)
        image = (image - image_min) / (image_max - image_min)

        image_patches = []
        if len(image.shape) == 3:
            for x in range(image.shape[2]):
                image_patches.append(image[x][:patch_size, :patch_size].flatten())
                image_patches.append(image[x][:patch_size, -patch_size:].flatten())
                image_patches.append(image[x][-patch_size:, :patch_size].flatten())
                image_patches.append(image[x][-patch_size:, -patch_size:].flatten())
        else:
            image_patches.append(image[:patch_size, :patch_size].flatten())
            image_patches.append(image[:patch_size, -patch_size:].flatten())
            image_patches.append(image[-patch_size:, :patch_size].flatten())
            image_patches.append(image[-patch_size:, -patch_size:].flatten())
        image_patch_all = np.asarray(image_patches).flatten()
        del image_patches

        noise_max = np.max(image_patch_all)
        noise_threshold = 1.25 * noise_max
        noise_acq = np.std(image[np.where(image <= noise_threshold)])

        self.noise_acq = noise_acq


# from amri.dat2py import dat2py_main as dat2py_main_pulseq
# from scipy.misc import imrotate
#
# lut = LUT()
# time_seconds_remaining = 690  # E1/2/3: 690/810/1350 (11.5 mins/13.5 mins/22.5 mins)
#
# # All
# _, image_space = dat2py_main_pulseq.main('/Users/sravan953/Downloads/AMRI/isp.dat', verbose=False)
# sos = dat2py_main_pulseq.get_image(image_space=image_space)
# sos = imrotate(sos, angle=0)  # Rotate by 0 because imrotate scales image to 0-255
# lut.update_lut_from_image(image=sos, patch_size=2)
# seq_objs, time_seconds_remaining_modified = lut.get_last_n_sequences(time_seconds_remaining=time_seconds_remaining,
#                                                                      last_n=3)
# if time_seconds_remaining != time_seconds_remaining_modified:
#     time_seconds_remaining = time_seconds_remaining_modified
#
# # T2
# _, image_space = dat2py_main_pulseq.main('/Users/sravan953/Downloads/slices/scan_1.dat', verbose=False)
# sos = dat2py_main_pulseq.get_image(image_space=image_space)
# sos_min = np.amin(sos)
# sos_max = np.amax(sos)
# sos = (sos - sos_min) / (sos_max - sos_min)
# lut.update_lut_from_image(sos)
# seq_objs, time_seconds_remaining_modified = lut.get_last_n_sequences(time_seconds_remaining=time_seconds_remaining,
#                                                                      last_n=2)
# if time_seconds_remaining != time_seconds_remaining_modified:
#     time_seconds_remaining = time_seconds_remaining_modified
#
# # T2*
# _, image_space = dat2py_main_pulseq.main('/Users/sravan953/Downloads/slices/scan_2.dat', verbose=False)
# sos = dat2py_main_pulseq.get_image(image_space=image_space)
# sos_min = np.amin(sos)
# sos_max = np.amax(sos)
# sos = (sos - sos_min) / (sos_max - sos_min)
# sos = imrotate(sos, angle=0)  # Rotate by 0 because imrotate scales image to 0-255
# lut.update_lut_from_image(sos)
# seq_objs, time_seconds_remaining_modified = lut.get_last_n_sequences(time_seconds_remaining=time_seconds_remaining,
#                                                                      last_n=1)
# if time_seconds_remaining != time_seconds_remaining_modified:
#     time_seconds_remaining = time_seconds_remaining_modified

# TODO
# Figure out acq time constraints for LUT
# Plug sequences into AMRI
# T1 - same as before, flip(5-20) (DONE)
# T2 - TR(1500-3000), TE(100-350), flip unchanged (DONE)
# T2* - same as before
# 1305.6 (max), 680(min)
