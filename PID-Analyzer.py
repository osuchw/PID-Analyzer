#!/usr/bin/env python
import argparse
import logging
import os
import time
import matplotlib.pyplot as plt

from pidanalyze import __version__, loader, plotter, analyzer

# ----------------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <florian.melsheimer@gmx.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Florian Melsheimer
# ----------------------------------------------------------------------------------


def run_analysis(log_file_path, plot_name, blackbox_decode, show, noise_bounds):

    tmp_dir = os.path.join(os.path.dirname(log_file_path), plot_name)
    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)

    loglist = loader.decode(log_file_path, tmp_dir, blackbox_decode)
    heads = loader.beheader(loglist, tmp_dir)

    figs = []
    for head in heads:
        fpath = head["tempFile"][:-3] + "01.csv"

        logging.info("Reading: Log %s", head["logNum"])
        data = loader.readcsv(fpath)
        traces = loader.find_traces(data, head)

        logging.info("Processing:")
        analyzed = []
        for trace in traces:
            logging.info(trace["name"] + "...   ")
            analyzed.append(analyzer.Trace(trace))
        roll, pitch, yaw = analyzed

        fig_resp = plotter.plot_all_resp(
            fpath, head, [roll, pitch, yaw], analyzer.Trace.threshold
        )
        logging.info("Saving response plot as image...")
        fig_resp.savefig(f"{fpath[:-13]}.{plot_name}_{head['logNum']}_response.png")

        fig_noise = plotter.plot_all_noise(
            fpath, head, [roll, pitch, yaw], noise_bounds
        )
        logging.info("Saving noise plot as image...")
        fig_noise.savefig(f"{fpath[:-13]}.{plot_name}_{head['logNum']}_noise.png")

        figs.append([fig_resp, fig_noise])
        if show != "Y":
            plt.cla()
            plt.clf()

    loader.deletejunk(loglist)
    logging.info("Analysis complete, showing plot. (Close plot to exit.)")


def strip_quotes(filepath):
    """Strips single or double quotes and extra whitespace from a string."""
    return filepath.strip().strip("'").strip('"')


def clean_path(path):
    return os.path.abspath(os.path.expanduser(strip_quotes(path)))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s %(asctime)s %(filename)s:%(lineno)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--log",
        action="append",
        help="BBL log file(s) to analyse. Omit for interactive prompt.",
    )
    parser.add_argument("-n", "--name", default="tmp", help="Plot name.")
    parser.add_argument(
        "--blackbox_decode",
        default=os.path.join(os.getcwd(), "Blackbox_decode.exe"),
        help="Path to Blackbox_decode.exe.",
    )
    parser.add_argument(
        "-s",
        "--show",
        default="Y",
        help="Y = show plot window when done.\nN = Do not. \nDefault = Y",
    )
    parser.add_argument(
        "-nb",
        "--noise_bounds",
        default="[[1.,10.1],[1.,100.],[1.,100.],[0.,4.]]",
        help='bounds of plots in noise analysis. use "auto" for autoscaling. \n default=[[1.,10.1],[1.,100.],[1.,100.],[0.,4.]]',
    )
    args = parser.parse_args()

    blackbox_decode_path = clean_path(args.blackbox_decode)
    try:
        args.noise_bounds = eval(args.noise_bounds)

    except:
        args.noise_bounds = args.noise_bounds
    if not os.path.isfile(blackbox_decode_path):
        parser.error(
            (
                "Could not find Blackbox_decode.exe (used to generate CSVs from "
                "your BBL file) at %s. You may need to install it from "
                "https://github.com/cleanflight/blackbox-tools/releases."
            )
            % blackbox_decode_path
        )
    logging.info("Decoding with %r" % blackbox_decode_path)

    logging.info("PID Analyzer: %s", __version__)
    logging.info("Hello Pilot!")

    if args.log:
        for log_path in args.log:
            run_analysis(
                clean_path(log_path),
                args.name,
                args.blackbox_decode,
                args.show,
                args.noise_bounds,
            )
        if args.show.upper() == "Y":
            plt.show()
        else:
            plt.cla()
            plt.clf()

    else:
        while True:
            logging.info("Interactive mode: Enter log file, or type close when done.")

            try:
                time.sleep(0.1)
                raw_path = input("Blackbox log file path (type or drop here): ")

                if raw_path == "close":
                    logging.info("Goodbye!")
                    break

                raw_paths = (
                    strip_quotes(raw_path).replace("''", '""').split('""')
                )  # seperate multiple paths
                name = input("Optional plot name:") or args.name
                showplt = input("Show plot window when done? [Y]/N") or args.show
                noise_bounds = (
                    input(
                        'Bounds on noise plot: [default/last] | copy and edit | "auto"\nCurrent: '
                        + str(args.noise_bounds)
                        + "\n"
                    )
                    or args.noise_bounds
                )

                args.show = showplt.upper()
                try:
                    args.noise_bounds = eval(noise_bounds)

                except:
                    args.noise_bounds = noise_bounds

            except (EOFError, KeyboardInterrupt):
                logging.info("Goodbye!")
                break

            for p in raw_paths:
                if os.path.isfile(clean_path(p)):
                    run_analysis(
                        clean_path(p),
                        name,
                        args.blackbox_decode,
                        args.show,
                        args.noise_bounds,
                    )
                else:
                    logging.info("No valid input path!")
            if args.show == "Y":
                plt.show()
            else:
                plt.cla()
                plt.clf()
