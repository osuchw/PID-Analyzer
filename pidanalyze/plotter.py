import logging
import numpy as np
from matplotlib import rcParams
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.colors as colors

from . import __version__


def check_lims_list(lims):
    if type(lims) is list:
        l = np.array(lims)
        if np.shape(l) == (4, 2):
            ll = l[:, 1] - l[:, 0]
            if np.sum(np.abs((ll - np.abs(ll)))) == 0:
                return True
    else:
        logging.warning("noise_bounds is no valid list")
        return False


def plot_all_noise(fpath, headdict, traces, lims):
    # style='fancy' gives 2d hist for response
    textsize = 7
    rcParams.update({"font.size": 9})

    logging.info("Making noise plot...")
    fig = plt.figure(
        "Noise plot: Log number: "
        + headdict["logNum"]
        + "          "
        + fpath,
        figsize=(16, 8),
    )
    ### gridspec devides window into 25 horizontal, 31 vertical fields
    gs1 = GridSpec(
        25,
        3 * 10 + 2,
        wspace=0.6,
        hspace=0.7,
        left=0.04,
        right=1.0,
        bottom=0.05,
        top=0.97,
    )

    max_noise_gyro = (
        np.max(
            [
                traces[0].noise_gyro["max"],
                traces[1].noise_gyro["max"],
                traces[2].noise_gyro["max"],
            ]
        )
        + 1.0
    )
    max_noise_debug = (
        np.max(
            [
                traces[0].noise_debug["max"],
                traces[1].noise_debug["max"],
                traces[2].noise_debug["max"],
            ]
        )
        + 1.0
    )
    max_noise_d = (
        np.max(
            [
                traces[0].noise_d["max"],
                traces[1].noise_d["max"],
                traces[2].noise_d["max"],
            ]
        )
        + 1.0
    )

    meanspec = np.array(
        [
            traces[0].noise_gyro["hist2d_sm"].mean(axis=1).flatten(),
            traces[1].noise_gyro["hist2d_sm"].mean(axis=1).flatten(),
            traces[2].noise_gyro["hist2d_sm"].mean(axis=1).flatten(),
        ],
        dtype=np.float64,
    )
    thresh = 100.0
    mask = traces[0].to_mask(
        traces[0].noise_gyro["freq_axis"].clip(thresh - 1e-9, thresh)
    )
    meanspec_max = np.max(meanspec * mask[:-1])

    if not check_lims_list(lims):
        lims = np.array(
            [
                [1, max_noise_gyro],
                [1, max_noise_debug],
                [1, max_noise_d],
                [0, meanspec_max * 1.5],
            ]
        )
        if lims[0, 1] == 1:
            lims[0, 1] = 100.0
        if lims[1, 1] == 1:
            lims[1, 1] = 100.0
        if lims[2, 1] == 1:
            lims[2, 1] = 100.0
    else:
        lims = np.array(lims)

    cax_gyro = plt.subplot(gs1[0, 0:7])
    cax_debug = plt.subplot(gs1[0, 8:15])
    cax_d = plt.subplot(gs1[0, 16:23])
    cmap = "viridis"

    axes_gyro = []
    axes_debug = []
    axes_d = []
    axes_trans = []

    for i, tr in enumerate(traces):
        if tr.noise_gyro["freq_axis"][-1] > 1000:
            pltlim = [0, 1000]
        else:
            pltlim = [
                tr.noise_gyro["freq_axis"][-0],
                tr.noise_gyro["freq_axis"][-1],
            ]
        # gyro plots
        ax0 = plt.subplot(gs1[1 + i * 8 : 1 + i * 8 + 8, 0:7])
        if len(axes_gyro):
            axes_gyro[0].get_shared_x_axes().join(axes_gyro[0], ax0)
        axes_gyro.append(ax0)
        ax0.set_title("gyro " + tr.name, y=0.88, color="w")
        pc0 = plt.pcolormesh(
            tr.noise_gyro["throt_axis"],
            tr.noise_gyro["freq_axis"],
            tr.noise_gyro["hist2d_sm"] + 1.0,
            norm=colors.LogNorm(vmin=lims[0, 0], vmax=lims[0, 1]),
            cmap=cmap,
        )
        ax0.set_ylabel("frequency in Hz")
        ax0.grid()
        ax0.set_ylim(pltlim)
        if i < 2:
            plt.setp(ax0.get_xticklabels(), visible=False)
        else:
            ax0.set_xlabel("throttle in %")

        fig.colorbar(pc0, cax_gyro, orientation="horizontal")
        cax_gyro.xaxis.set_ticks_position("top")
        cax_gyro.xaxis.set_tick_params(pad=-0.5)

        if max_noise_gyro == 1.0:
            ax0.text(
                0.5,
                0.5,
                "no gyro[" + str(i) + "] trace found!\n",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax0.transAxes,
                fontdict={"color": "white"},
            )

        # debug plots
        ax1 = plt.subplot(gs1[1 + i * 8 : 1 + i * 8 + 8, 8:15])
        if len(axes_debug):
            axes_debug[0].get_shared_x_axes().join(axes_debug[0], ax1)
        axes_debug.append(ax1)
        ax1.set_title("debug " + tr.name, y=0.88, color="w")
        pc1 = plt.pcolormesh(
            tr.noise_debug["throt_axis"],
            tr.noise_debug["freq_axis"],
            tr.noise_debug["hist2d_sm"] + 1.0,
            norm=colors.LogNorm(vmin=lims[1, 0], vmax=lims[1, 1]),
            cmap=cmap,
        )
        ax1.set_ylabel("frequency in Hz")
        ax1.grid()
        ax1.set_ylim(pltlim)
        if i < 2:
            plt.setp(ax1.get_xticklabels(), visible=False)
        else:
            ax1.set_xlabel("throttle in %")

        fig.colorbar(pc1, cax_debug, orientation="horizontal")
        cax_debug.xaxis.set_ticks_position("top")
        cax_debug.xaxis.set_tick_params(pad=-0.5)

        if max_noise_debug == 1.0:
            ax1.text(
                0.5,
                0.5,
                "no debug[" + str(i) + "] trace found!\n"
                "To get transmission of\n"
                "- all filters: set debug_mode = NOTCH\n"
                "- LPF only: set debug_mode = GYRO",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax1.transAxes,
                fontdict={"color": "white"},
            )

        if i < 2:
            # dterm plots
            ax2 = plt.subplot(gs1[1 + i * 8 : 1 + i * 8 + 8, 16:23])
            if len(axes_d):
                axes_d[0].get_shared_x_axes().join(axes_d[0], ax2)
            axes_d.append(ax2)
            ax2.set_title("D-term " + tr.name, y=0.88, color="w")
            pc2 = plt.pcolormesh(
                tr.noise_d["throt_axis"],
                tr.noise_d["freq_axis"],
                tr.noise_d["hist2d_sm"] + 1.0,
                norm=colors.LogNorm(vmin=lims[2, 0], vmax=lims[2, 1]),
                cmap=cmap,
            )
            ax2.set_ylabel("frequency in Hz")
            ax2.grid()
            ax2.set_ylim(pltlim)
            plt.setp(ax2.get_xticklabels(), visible=False)

            fig.colorbar(pc2, cax_d, orientation="horizontal")
            cax_d.xaxis.set_ticks_position("top")
            cax_d.xaxis.set_tick_params(pad=-0.5)

            if max_noise_d == 1.0:
                ax2.text(
                    0.5,
                    0.5,
                    "no D[" + str(i) + "] trace found!\n",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=ax2.transAxes,
                    fontdict={"color": "white"},
                )

        else:
            # throttle plots
            ax21 = plt.subplot(gs1[1 + i * 8 : 1 + i * 8 + 4, 16:23])
            ax22 = plt.subplot(gs1[1 + i * 8 + 5 : 1 + i * 8 + 8, 16:23])
            ax21.bar(
                tr.throt_scale[:-1],
                tr.throt_hist * 100.0,
                width=1.0,
                align="edge",
                color="black",
                alpha=0.2,
                label="throttle distribution",
            )
            axes_d[0].get_shared_x_axes().join(axes_d[0], ax21)
            ax21.vlines(
                headdict["tpa_percent"],
                0.0,
                100.0,
                label="tpa",
                colors="red",
                alpha=0.5,
            )
            ax21.grid()
            ax21.set_ylim([0.0, np.max(tr.throt_hist) * 100.0 * 1.1])
            ax21.set_xlabel("throttle in %")
            ax21.set_ylabel("usage %")
            ax21.set_xlim([0.0, 100.0])
            handles, labels = ax21.get_legend_handles_labels()
            ax21.legend(handles[::-1], labels[::-1])
            ax22.fill_between(
                tr.time,
                0.0,
                tr.throttle,
                label="throttle input",
                facecolors="black",
                alpha=0.2,
            )
            ax22.hlines(
                headdict["tpa_percent"],
                tr.time[0],
                tr.time[-1],
                label="tpa",
                colors="red",
                alpha=0.5,
            )

            ax22.set_ylabel("throttle in %")
            ax22.legend()
            ax22.grid()
            ax22.set_ylim([0.0, 100.0])
            ax22.set_xlim([tr.time[0], tr.time[-1]])
            ax22.set_xlabel("time in s")

        # transmission plots
        ax3 = plt.subplot(gs1[1 + i * 8 : 1 + i * 8 + 8, 24:30])
        if len(axes_trans):
            axes_trans[0].get_shared_x_axes().join(axes_trans[0], ax3)
        axes_trans.append(ax3)
        ax3.fill_between(
            tr.noise_gyro["freq_axis"][:-1],
            0,
            meanspec[i],
            label=tr.name + " gyro noise",
            alpha=0.2,
        )
        ax3.set_ylim(lims[3])
        ax3.set_ylabel(tr.name + " gyro noise a.u.")
        ax3.grid()
        ax3r = plt.twinx(ax3)
        ax3r.plot(
            tr.noise_gyro["freq_axis"][:-1],
            tr.filter_trans * 100.0,
            label=tr.name + " filter transmission",
        )
        ax3r.set_ylabel("transmission in %")
        ax3r.set_ylim([0.0, 100.0])
        ax3r.set_xlim(
            [tr.noise_gyro["freq_axis"][0], tr.noise_gyro["freq_axis"][-2]]
        )
        lines, labels = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3r.get_legend_handles_labels()
        ax3r.legend(lines + lines2, labels + labels2, loc=1)
        if i < 2:
            plt.setp(ax3.get_xticklabels(), visible=False)
        else:
            ax3.set_xlabel("frequency in hz")

    meanfreq = 1.0 / (traces[0].time[1] - traces[0].time[0])
    ax4 = plt.subplot(gs1[12, -1])
    t = (
        "PID-Analyzer "
        + __version__
        + "| Betaflight: Version "
        + headdict["version"]
        + " | Craftname: "
        + headdict["craftName"]
        + " | meanFreq: "
        + str(int(meanfreq))
        + " | rcRate/Expo: "
        + headdict["rcRate"]
        + "/"
        + headdict["rcExpo"]
        + "\nrcYawRate/Expo: "
        + headdict["rcYawRate"]
        + "/"
        + headdict["rcYawExpo"]
        + " | deadBand: "
        + headdict["deadBand"]
        + " | yawDeadBand: "
        + headdict["yawDeadBand"]
        + " | Throttle min/tpa/max: "
        + headdict["minThrottle"]
        + "/"
        + headdict["tpa_breakpoint"]
        + "/"
        + headdict["maxThrottle"]
        + " | dynThrPID: "
        + headdict["dynThrottle"]
        + "| D-TermSP: "
        + headdict["dTermSetPoint"]
        + "| vbatComp: "
        + headdict["vbatComp"]
        + " | debug "
        + headdict["debug_mode"]
    )

    ax4.text(
        0,
        0,
        t,
        ha="left",
        va="center",
        rotation=90,
        color="grey",
        alpha=0.5,
        fontsize=textsize,
    )
    ax4.axis("off")

    ax5l = plt.subplot(gs1[:1, 24:27])
    ax5r = plt.subplot(gs1[:1, 27:30])
    ax5l.axis("off")
    ax5r.axis("off")
    filt_settings_l = (
        "G lpf type: "
        + headdict["gyro_lpf"]
        + " at "
        + headdict["gyro_lowpass_hz"]
        + "\n"
        + "G notch at: "
        + headdict["gyro_notch_hz"]
        + " cut "
        + headdict["gyro_notch_cutoff"]
        + "\n"
        "gyro lpf 2: " + headdict["gyro_lowpass_type"]
    )
    filt_settings_r = (
        "| D lpf type: "
        + headdict["dterm_filter_type"]
        + " at "
        + headdict["dterm_lpf_hz"]
        + "\n"
        + "| D notch at: "
        + headdict["dterm_notch_hz"]
        + " cut "
        + headdict["dterm_notch_cutoff"]
        + "\n"
        + "| Yaw lpf at: "
        + headdict["yaw_lpf_hz"]
    )

    ax5l.text(0, 0, filt_settings_l, ha="left", fontsize=textsize)
    ax5r.text(0, 0, filt_settings_r, ha="left", fontsize=textsize)

    return fig

def plot_all_resp(fpath, headdict, traces, threshold, style="ra"):
    textsize = 7
    titelsize = 10
    rcParams.update({"font.size": 9})
    logging.info("Making PID plot...")
    fig = plt.figure(
        "Response plot: Log number: "
        + headdict["logNum"]
        + "          "
        + fpath,
        figsize=(16, 8),
    )
    ### gridspec devides window into 24 horizontal, 3*10 vertical fields
    gs1 = GridSpec(
        24,
        3 * 10,
        wspace=0.6,
        hspace=0.7,
        left=0.04,
        right=1.0,
        bottom=0.05,
        top=0.97,
    )

    for i, tr in enumerate(traces):
        ax0 = plt.subplot(gs1[0:6, i * 10 : i * 10 + 9])
        plt.title(tr.name)
        plt.plot(tr.time, tr.gyro, label=tr.name + " gyro")
        plt.plot(tr.time, tr.input, label=tr.name + " loop input")
        plt.ylabel("degrees/second")
        ax0.get_yaxis().set_label_coords(-0.1, 0.5)
        plt.grid()
        tracelim = np.max([np.abs(tr.gyro), np.abs(tr.input)])
        plt.ylim([-tracelim * 1.1, tracelim * 1.1])
        plt.legend(loc=1)
        plt.setp(ax0.get_xticklabels(), visible=False)

        ax1 = plt.subplot(gs1[6:8, i * 10 : i * 10 + 9], sharex=ax0)
        plt.hlines(
            headdict["tpa_percent"],
            tr.time[0],
            tr.time[-1],
            label="tpa",
            colors="red",
            alpha=0.5,
        )
        plt.fill_between(
            tr.time, 0.0, tr.throttle, label="throttle", color="grey", alpha=0.2
        )
        plt.ylabel("throttle %")
        ax1.get_yaxis().set_label_coords(-0.1, 0.5)
        plt.grid()
        plt.xlim([tr.time[0], tr.time[-1]])
        plt.ylim([0, 100])
        plt.legend(loc=1)
        plt.xlabel("log time in s")

        if style == "raw":
            ###old raw data plot.
            plt.setp(ax1.get_xticklabels(), visible=False)
            ax2 = plt.subplot(gs1[9:16, i * 10 : i * 10 + 9], sharex=ax0)
            plt.pcolormesh(
                tr.avr_t, tr.time_resp, np.transpose(tr.spec_sm), vmin=0, vmax=2.0
            )
            plt.ylabel("response time in s")
            ax2.get_yaxis().set_label_coords(-0.1, 0.5)
            plt.xlabel("log time in s")
            plt.xlim([tr.avr_t[0], tr.avr_t[-1]])

        else:
            ###response vs throttle plot. more useful.
            ax2 = plt.subplot(gs1[9:16, i * 10 : i * 10 + 9])
            plt.title(tr.name + " response", y=0.88, color="w")
            plt.pcolormesh(
                tr.thr_response["throt_scale"],
                tr.time_resp,
                tr.thr_response["hist2d_norm"],
                vmin=0.0,
                vmax=2.0,
            )
            plt.ylabel("response time in s")
            ax2.get_yaxis().set_label_coords(-0.1, 0.5)
            plt.xlabel("throttle in %")
            plt.xlim([0.0, 100.0])

        theCM = plt.cm.get_cmap("Blues")
        theCM._init()
        alphas = np.abs(np.linspace(0.0, 0.5, theCM.N, dtype=np.float64))
        theCM._lut[:-3, -1] = alphas
        ax3 = plt.subplot(gs1[17:, i * 10 : i * 10 + 9])
        plt.contourf(
            *tr.resp_low[2],
            cmap=theCM,
            linestyles=None,
            antialiased=True,
            levels=np.linspace(0, 1, 20, dtype=np.float64)
        )
        plt.plot(
            tr.time_resp,
            tr.resp_low[0],
            label=tr.name
            + " step response "
            + "(<"
            + str(int(threshold))
            + ") "
            + " PID "
            + headdict[tr.name + "PID"],
        )

        if tr.high_mask.sum() > 0:
            theCM = plt.cm.get_cmap("Oranges")
            theCM._init()
            alphas = np.abs(np.linspace(0.0, 0.5, theCM.N, dtype=np.float64))
            theCM._lut[:-3, -1] = alphas
            plt.contourf(
                *tr.resp_high[2],
                cmap=theCM,
                linestyles=None,
                antialiased=True,
                levels=np.linspace(0, 1, 20, dtype=np.float64)
            )
            plt.plot(
                tr.time_resp,
                tr.resp_high[0],
                label=tr.name
                + " step response "
                + "(>"
                + str(int(threshold))
                + ") "
                + " PID "
                + headdict[tr.name + "PID"],
            )
        plt.xlim([-0.001, 0.501])

        plt.legend(loc=1)
        plt.ylim([0.0, 2])
        plt.ylabel("strength")
        ax3.get_yaxis().set_label_coords(-0.1, 0.5)
        plt.xlabel("response time in s")

        plt.grid()

    meanfreq = 1.0 / (traces[0].time[1] - traces[0].time[0])
    ax4 = plt.subplot(gs1[12, -1])
    t = (
        "PID-Analyzer "
        + __version__
        + " | Betaflight: Version "
        + headdict["version"]
        + " | Craftname: "
        + headdict["craftName"]
        + " | meanFreq: "
        + str(int(meanfreq))
        + " | rcRate/Expo: "
        + headdict["rcRate"]
        + "/"
        + headdict["rcExpo"]
        + "\nrcYawRate/Expo: "
        + headdict["rcYawRate"]
        + "/"
        + headdict["rcYawExpo"]
        + " | deadBand: "
        + headdict["deadBand"]
        + " | yawDeadBand: "
        + headdict["yawDeadBand"]
        + " | Throttle min/tpa/max: "
        + headdict["minThrottle"]
        + "/"
        + headdict["tpa_breakpoint"]
        + "/"
        + headdict["maxThrottle"]
        + " | dynThrPID: "
        + headdict["dynThrottle"]
        + "| D-TermSP: "
        + headdict["dTermSetPoint"]
        + "| vbatComp: "
        + headdict["vbatComp"]
    )

    plt.text(
        0,
        0,
        t,
        ha="left",
        va="center",
        rotation=90,
        color="grey",
        alpha=0.5,
        fontsize=textsize,
    )
    ax4.axis("off")
    return fig

