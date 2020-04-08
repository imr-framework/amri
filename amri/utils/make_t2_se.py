"""
Author: Keerthi Sravan Ravi
"""


from math import pi

import numpy as np

from pypulseq.Sequence.sequence import Sequence
from pypulseq.calc_duration import calc_duration
from pypulseq.make_adc import makeadc
from pypulseq.make_delay import make_delay
from pypulseq.make_sinc import make_sinc_pulse
from pypulseq.make_trap import make_trapezoid
from pypulseq.opts import Opts


def make_t2_se(te, tr, flip_deg, Nx=128, Ny=128, n_slices=3, rf_offset=0):
    kwargs_for_opts = {"max_grad": 32, "max_slew": 130, "grad_raster_time": 10e-6, "rf_ring_down_time": 10e-6,
                       "rf_dead_time": 100e-6}
    system = Opts(kwargs_for_opts)
    seq = Sequence(system)

    fov = 220e-3
    slice_thickness = 5e-3
    slice_gap = 15e-3

    delta_z = n_slices * slice_gap
    z = np.linspace((-delta_z / 2), (delta_z / 2), n_slices) + rf_offset

    # =========
    # RF90, RF180
    # =========
    flip90 = round(flip_deg * pi / 180, 3)
    kwargs_for_sinc90 = {"flip_angle": flip90, "system": system, "duration": 4e-3, "slice_thickness": slice_thickness,
                         "apodization": 0.5, "time_bw_product": 4}
    rf90, gz90 = make_sinc_pulse(kwargs_for_sinc90, 2)

    flip180 = 180 * pi / 180
    kwargs_for_sinc = {"flip_angle": flip180, "system": system, "duration": 2.5e-3, "slice_thickness": slice_thickness,
                       "apodization": 0.5, "time_bw_product": 4, "phase_offset": 90 * pi / 180}
    rf180, gz180 = make_sinc_pulse(kwargs_for_sinc, 2)

    # =========
    # Gz Rephase
    # =========
    kwargs_for_gz_reph = {"channel": 'z', "system": system, "area": -gz90.area / 2, "duration": 2.5e-3}
    gz_reph = make_trapezoid(kwargs_for_gz_reph)

    # =========
    # Gx, ADC
    # =========
    delta_k = 1 / fov
    k_width = Nx * delta_k
    readout_time = 6.4e-3
    kwargs_for_gx = {"channel": 'x', "system": system, "flat_area": k_width, "flat_time": readout_time}
    gx = make_trapezoid(kwargs_for_gx)
    kwargs_for_adc = {"num_samples": Nx, "duration": gx.flat_time, "delay": gx.rise_time}
    adc = makeadc(kwargs_for_adc)

    # =========
    # Gx Prephase
    # =========
    kwargs_for_gxpre = {"channel": 'x', "system": system, "flat_area": k_width / 2, "flat_time": readout_time / 2}
    gx_pre = make_trapezoid(kwargs_for_gxpre)

    # =========
    # Gy Prephase
    # =========
    phase_areas = (np.arange(Ny) - (Ny / 2)) * delta_k
    kwargs_for_gy_pre = {"channel": 'y', "system": system, "area": phase_areas[-1], "duration": 2e-3}
    gy_pre = make_trapezoid(kwargs_for_gy_pre)

    # =========
    # Gz Spoil
    # =========
    pre_time = 8e-4
    kwargs_for_gz_spoil = {"channel": 'z', "system": system, "area": gz90.area * 4, "duration": pre_time * 4}
    gz_spoil = make_trapezoid(kwargs_for_gz_spoil)

    # =========
    # Delays
    # =========
    TE, TR = te, tr
    tau = TE / 2
    delay1 = tau - calc_duration(rf90) / 2 - calc_duration(gx_pre) - calc_duration(gz_spoil) - calc_duration(rf180) / 2
    delay1 = make_delay(delay1)
    delay2 = tau - calc_duration(rf180) / 2 - calc_duration(gz_spoil) - calc_duration(gx) / 2
    delay2 = make_delay(delay2)
    delay_TR = TR - calc_duration(rf90) / 2 - calc_duration(gx) / 2 - TE - calc_duration(gy_pre)
    delay_TR = make_delay(delay_TR)

    nsa = 1
    for k in range(nsa):
        for j in range(n_slices):
            freq_offset = gz90.amplitude * z[j]
            rf90.freq_offset = freq_offset
            freq_offset = gz180.amplitude * z[j]
            rf180.freq_offset = freq_offset
            for i in range(Ny):
                seq.add_block(rf90, gz90)
                kwargs_for_gy_pre = {"channel": 'y', "system": system, "area": phase_areas[-i - 1], "duration": 2e-3}
                gy_pre = make_trapezoid(kwargs_for_gy_pre)
                seq.add_block(gx_pre, gy_pre, gz_reph)
                seq.add_block(delay1)
                seq.add_block(gz_spoil)
                seq.add_block(rf180, gz180)
                seq.add_block(gz_spoil)
                seq.add_block(delay2)
                seq.add_block(gx, adc)
                kwargs_for_gy_pre = {"channel": 'y', "system": system, "area": -phase_areas[-j - 1], "duration": 2e-3}
                gy_pre = make_trapezoid(kwargs_for_gy_pre)
                seq.add_block(gy_pre, gz_spoil)
                seq.add_block(delay_TR)

    seq.te = TE
    seq.tr = TR
    seq.flip = (flip90, flip180)
    seq.Ny = Ny
    seq.slices = n_slices
    seq.nsa = nsa

    return seq


# a = make_t2_se(100e-3, 1500e-3, 90, Nx=128, Ny=128, n_slices=3, rf_offset=0)
# a.write('/Users/sravan953/Desktop/external.seq')
