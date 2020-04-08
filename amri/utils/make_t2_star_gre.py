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


def make_t2_star_se(te, tr, flip_deg, Nx=128, Ny=128, n_slices=3, rf_offset=0):
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
    # RF90, Gz
    # =========
    flip = round(flip_deg * pi / 180, 3)
    kwargs_for_sinc = {"flip_angle": flip, "system": system, "duration": 4e-3, "slice_thickness": slice_thickness,
                       "freq_offset": rf_offset, "apodization": 0.5, "time_bw_product": 4}
    rf, gz = make_sinc_pulse(kwargs_for_sinc, 2)

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
    kwargs_for_gxpre = {"channel": 'x', "system": system, "area": -gx.area / 2, "duration": 2e-3}
    gx_pre = make_trapezoid(kwargs_for_gxpre)

    # =========
    # Gz Rephase
    # =========
    kwargs_for_gz_reph = {"channel": 'z', "system": system, "area": -gz.area / 2, "duration": 2e-3}
    gz_reph = make_trapezoid(kwargs_for_gz_reph)

    # =========
    # Delays
    # =========
    TE, TR = te, tr
    delay_TE = TE - calc_duration(rf) / 2 - calc_duration(gx_pre) - calc_duration(gx) / 2
    delay_TE = make_delay(delay_TE)
    delay_TR = TR - calc_duration(rf) / 2 - calc_duration(gx) / 2 - TE
    delay_TR = make_delay(delay_TR)

    phase_areas = (np.arange(Ny) - (Ny / 2)) * delta_k

    nsa = 1
    for k in range(nsa):
        for j in range(n_slices):
            freq_offset = gz.amplitude * z[j]
            rf.freq_offset = freq_offset
            for i in range(Ny):
                seq.add_block(rf, gz)
                kwargs_for_gy_pre = {"channel": 'y', "system": system, "area": phase_areas[i], "duration": 2e-3}
                gy_pre = make_trapezoid(kwargs_for_gy_pre)
                seq.add_block(gx_pre, gy_pre, gz_reph)
                seq.add_block(delay_TE)
                seq.add_block(gx, adc)
                seq.add_block(delay_TR)
                kwargs_for_gy_pre = {"channel": 'y', "system": system, "area": -phase_areas[-i - 1], "duration": 2e-3}
                gy_pre = make_trapezoid(kwargs_for_gy_pre)
                seq.add_block(gy_pre)

    seq.te = TE
    seq.tr = TR
    seq.flip = flip
    seq.Ny = Ny
    seq.slices = n_slices
    seq.nsa = nsa

    return seq


# a = make_t2_star_se(50e-3, 300e-3, 11.66, Nx=128, Ny=128, n_slices=3, rf_offset=0)
# a.write('/Users/sravan953/Desktop/external.seq')
