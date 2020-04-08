"""
Author: Keerthi Sravan Ravi
This is starter code to demonstrate deg working example of deg multi-slice version of Gradient Recalled Echo sequence as an
imr-framework.pulseq implementation.
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


def make_isp_gre(te, tr, flip_deg, Nx=128, Ny=128, n_slices=3, rf_offset=0):
    kwargs_for_opts = {"max_grad": 32, "max_slew": 130, "grad_raster_time": 10e-6, "rf_ring_down_time": 10e-6,
                       "rf_dead_time": 100e-6}
    system = Opts(kwargs_for_opts)
    seq = Sequence(system)

    fov = 220e-3
    slice_thickness = 5e-3
    slice_gap = 15e-3

    delta_z = n_slices * slice_gap
    z = np.linspace((-delta_z / 2), (delta_z / 2), n_slices) + rf_offset

    flip = round(flip_deg * pi / 180, 3)
    kwargs_for_sinc = {"flip_angle": flip, "system": system, "duration": 4e-3, "slice_thickness": slice_thickness,
                       "freq_offset": rf_offset, "apodization": 0.5, "time_bw_product": 4}
    rf, gz = make_sinc_pulse(kwargs_for_sinc, 2)

    delta_k = 1 / fov
    k_width = Nx * delta_k
    readout_time = 6.4e-3
    kwargs_for_gx = {"channel": 'x', "system": system, "flat_area": k_width, "flat_time": readout_time}
    gx = make_trapezoid(kwargs_for_gx)
    kwargs_for_adc = {"num_samples": Nx, "duration": gx.flat_time, "delay": gx.rise_time}
    adc = makeadc(kwargs_for_adc)

    kwargs_for_gxpre = {"channel": 'x', "system": system, "area": -gx.area / 2, "duration": 2e-3}
    gx_pre = make_trapezoid(kwargs_for_gxpre)
    kwargs_for_gz_reph = {"channel": 'z', "system": system, "area": -gz.area / 2, "duration": 2e-3}
    gz_reph = make_trapezoid(kwargs_for_gz_reph)
    phase_areas = (np.arange(Ny) - (Ny / 2)) * delta_k

    TE, TR = te, tr
    delay_TE = TE - calc_duration(gx_pre) - calc_duration(gz) / 2 - calc_duration(gx) / 2
    delay_TR = TR - calc_duration(gx_pre) - calc_duration(gz) - calc_duration(gx) - delay_TE
    delay_TE = round(delay_TE, 5)
    delay_TR = round(delay_TR, 5)
    delay1 = make_delay(delay_TE)
    delay2 = make_delay(delay_TR)

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
                seq.add_block(delay1)
                seq.add_block(gx, adc)
                seq.add_block(delay2)

    seq.te = TE
    seq.tr = TR
    seq.flip = flip
    seq.Ny = Ny
    seq.slices = n_slices
    seq.nsa = nsa

    return seq
