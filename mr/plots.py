"""These functions generate handy plots."""

import matplotlib.pyplot as plt
import logging
import motion

logger = logging.getLogger(__name__)

def instant_gratification(func):
    """
    A decorator for plotting functions.
    NORMALLY: Direct the plotting function to the current axes, gca().
              When it's done, make the legend and show that plot. 
              (Instant gratificaiton!)
    BUT:      If the uses passes axes to plotting function, write on those axes
              and return them. The user has the option to draw a more complex 
              plot in multiple steps.
    """
    def wrapper(*args, **kwargs):
        if 'ax' not in kwargs:
            kwargs['ax'] = plt.gca()
            func(*args, **kwargs)
            if not kwargs['ax'].get_legend_handles_labels() == ([], []):
                plt.legend(loc='best')
            plt.show()
        else:
            return func(*args, **kwargs)
    return wrapper

@instant_gratification
def plot_drift(x, uncertainty=None, label='', ax=None):
    """Plot ensemble drift. To compare drifts of subsets, call multiple times
    with finish=False for all but the last call."""
    if uncertainty is not None:
        u = uncertainty # changing notation for brevity
        ax.fill_between(x[:, 0], x[:, 1] + u[:, 1], x[:, 1] - u[:, 1],
                        color='#DDDDDD')
        ax.fill_between(x[:, 0], x[:, 2] + u[:, 2], x[:, 2] - u[:, 2],
                        color='#DDDDDD')
    ax.plot(x[:, 0], x[:, 1], '-', label=label + ' X')
    ax.plot(x[:, 0], x[:, 2], '-', label=label + ' Y')
    ax.set_xlabel('time [frames]')
    ax.set_ylabel('drift [px]')
    return ax

@instant_gratification
def plot_traj(probes, mpp, superimpose=None, ax=None):
    """Plot traces of trajectories for each probe.
    Optionally superimpose it on a fram from the video."""
    probes = motion.cast_probes(probes)
    if superimpose:
        image = 1-plt.imread(superimpose)
        ax.imshow(image, cmap=plt.cm.gray)
        ax.set_xlim(0, image.shape[1])
        ax.set_ylim(0, image.shape[0])
        logger.info("Using units of px, not microns.")
        mpp = 1
        ax.set_xlabel('x [px]')
        ax.set_ylabel('y [px]')
    else:
        ax.set_xlabel('x [um]')
        ax.set_ylabel('y [um]')
    for traj in probes:
        ax.plot(mpp*traj[:, 1], mpp*traj[:, 2])
    return ax

@instant_gratification
def plot_msd(probes, mpp, fps, max_interval=None, ax=None):
    "Plot MSD for each probe individually."
    logger.info("%.3f microns per pixel, %d fps", mpp, fps)
    probes = motion.cast_probes(probes)
    msds = [motion.msd(traj, mpp, fps, max_interval, detail=False) \
            for traj in probes] 
    for counter, m in enumerate(msds):
        # Label only one instance for the plot legend.
        if counter == 0:
            ax.loglog(m[:, 0], m[:, 1], 'k.-', alpha=0.3,
                       label='individual probe MSDs')
        else:
            ax.loglog(m[:, 0], m[:, 1], 'k.-', alpha=0.3)
    _setup_msd_plot(ax)
    return ax

@instant_gratification
def plot_emsd(probes, mpp, fps, max_interval=None, powerlaw=True, ax=None):
    "Plot ensemble MSDs for probes."
    logger.info("%.3f microns per pixel, %d fps", mpp, fps)
    m = motion.ensemble_msd(probes, mpp, fps, max_interval)
    ax.loglog(m[:, 0], m[:, 1], 'ro-', 
              linewidth=3, label='ensemble MSD')
    if powerlaw:
        power, coeff = motion.fit_powerlaw(m)
        ax.loglog(m[:, 0], coeff*m[:, 0]**power, '-', 
                  color='#019AD2', linewidth=2,
                  label=_powerlaw_label(power, coeff))
    _setup_msd_plot(ax)
    return ax

@instant_gratification
def plot_bimodal_msd(probes, mpp, fps, max_interval=None, ax=None):
    """Plot individual MSDs with separate ensemble MSDs and power law fits
    for diffusive probes and localized probes."""
    probes = motion.cast_probes(probes)
    upper_branch, lower_branch, middle_branch = motion.split_branches(probes)
    plot_msd(upper_branch, mpp, fps, max_interval, ax=ax)
    plot_emsd(upper_branch, mpp, fps, max_interval, powerlaw=True, ax=ax)
    plot_msd(middle_branch, mpp, fps, max_interval, ax=ax)
    plot_msd(lower_branch, mpp, fps, max_interval, ax=ax)
    plot_emsd(lower_branch, mpp, fps, max_interval, powerlaw=True, ax=ax)
    return ax

def _setup_msd_plot(ax):
    # Label ticks with plain numbers, not scientific notation:
    ax.xaxis.set_major_formatter(plt.ScalarFormatter(useMathText=True))
    ax.yaxis.set_major_formatter(plt.ScalarFormatter(useMathText=True))
    ax.set_ylim(0.001, 100)
    logger.info('Limits of y range are manually set to %f - %f.', *plt.ylim())
    ax.set_xlabel('lag time [s]')
    ax.set_ylabel('msd [um$^2$]')

def _powerlaw_label(power, coeff):
    """Return a string suitable for a legend label, including power
    and D if motion is diffusive, but only power if it is subdiffusive."""
    DIFFUSIVE_THRESHOLD = 0.90
    label = 'power law fit\nn=' + '{:.2f}'.format(power)
    if power >= DIFFUSIVE_THRESHOLD:
        label += '  D=' + '{:.3f}'.format(coeff/4) + ' um$^2$/s'
    return label
    
    
