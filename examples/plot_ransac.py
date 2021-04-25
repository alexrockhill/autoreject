"""
===============================
Detect bad sensors using RANSAC
===============================

This example demonstrates how to use RANSAC [1]_ from the PREP pipeline to
detect bad sensors and repair them. Note that this implementation in
:mod:`autoreject` [2]_ is an extension of the original implementation and
works for MEG sensors as well.

References
----------
.. [1] Bigdely-Shamlo, N., Mullen, T., Kothe, C., Su, K. M., & Robbins, K. A.
       (2015). The PREP pipeline: standardized preprocessing for large-scale
       EEG analysis. Frontiers in neuroinformatics, 9, 16.
.. [2] Jas, M., Engemann, D. A., Bekhti, Y., Raimondo, F., & Gramfort, A.
       (2017). Autoreject: Automated artifact rejection for MEG and EEG data.
       NeuroImage, 159, 417-429.
"""

# Author: Mainak Jas <mjas@mgh.harvard.edu>
# License: BSD (3-clause)

###############################################################################
# For the purposes of this example, we shall use the MNE sample dataset.
# Therefore, let us make some MNE related imports.

import numpy as np
import os.path as op
import matplotlib.pyplot as plt

import mne
from mne import io
from mne import Epochs
from mne.datasets import sample
import autoreject

###############################################################################
# Let us now read in the raw `fif` file for MNE sample dataset.

data_path = sample.data_path()
sample_dir = op.join(data_path, 'MEG', 'sample')
raw_fname = op.join(sample_dir, 'sample_audvis_filt-0-40_raw.fif')
raw = io.read_raw_fif(raw_fname, preload=True)

###############################################################################
# We can then read in the events

event_fname = op.join(sample_dir, 'sample_audvis_filt-0-40_raw-eve.fif')
event_id = {'Auditory/Left': 1}
tmin, tmax = -0.2, 0.5

events = mne.read_events(event_fname)

###############################################################################
# And pick MEG channels for repairing. Currently, :mod:`autoreject` can repair
# only one channel type at a time.

raw.info['bads'] = []

###############################################################################
# Now, we can create epochs. The ``reject`` params will be set to ``None``
# because we do not want epochs to be dropped when instantiating
# :class:`mne.Epochs`.

raw.info['projs'] = list()  # remove proj, don't proj while interpolating
picks = mne.pick_types(raw.info, meg='grad', eeg=False, stim=False, eog=False,
                       include=[], exclude=[])
epochs = Epochs(raw, events, event_id, tmin, tmax,
                baseline=(None, 0), reject=None, picks=picks,
                verbose=False, detrend=0, preload=True)
epochs = epochs.pick_channels(np.array(epochs.ch_names)[np.arange(
    0, len(epochs.ch_names), 11)])  # decimate to save computation time


###############################################################################
# We run ``Ransac`` and the familiar ``fit_transform`` method.

ransac = autoreject.Ransac(verbose='progressbar', n_jobs=1)
epochs_clean = ransac.fit_transform(epochs)

###############################################################################
# We can also get the list of bad channels computed by ``Ransac``.

print('\n'.join(ransac.bad_chs_))

###############################################################################
# Then we compute the ``evoked`` before and after interpolation.

evoked = epochs.average()
evoked_clean = epochs_clean.average()

###############################################################################
# We will manually mark the bad channels just for plotting.

evoked.info['bads'] = ['MEG 2443']
evoked_clean.info['bads'] = ['MEG 2443']

###############################################################################
# Let us plot the results.

autoreject.set_matplotlib_defaults(plt)

fig, axes = plt.subplots(2, 1, figsize=(6, 6))

for ax in axes:
    ax.tick_params(axis='x', which='both', bottom='off', top='off')
    ax.tick_params(axis='y', which='both', left='off', right='off')

ylim = dict(grad=(-170, 200))
evoked.plot(exclude=[], axes=axes[0], ylim=ylim, show=False)
axes[0].set_title('Before RANSAC')
evoked_clean.plot(exclude=[], axes=axes[1], ylim=ylim)
axes[1].set_title('After RANSAC')
fig.tight_layout()

###############################################################################
# To top things up, we can also visualize the bad sensors for each trial using
# a heatmap.

bad_epochs = [False] * len(epochs)  # ransac just does channels not bad epochs
autoreject.RejectLog(bad_epochs, ransac.bad_log, epochs.ch_names).plot()
