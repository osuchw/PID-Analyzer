import logging
import os
import subprocess
import matplotlib.pyplot as plt

from . import plotter


LOG_MIN_BYTES = 500000



class BB_log:
    def __init__(self, log_file_path, name, blackbox_decode, show, noise_bounds):
        self.blackbox_decode_bin_path = blackbox_decode
        self.tmp_dir = os.path.join(os.path.dirname(log_file_path), name)
        if not os.path.isdir(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        self.name = name
        self.show = show
        self.noise_bounds = noise_bounds

        self.loglist = self.decode(log_file_path)
        self.heads = self.beheader(self.loglist)
        self.figs = self._csv_iter(self.heads)

        self.deletejunk(self.loglist)

    def deletejunk(self, loglist):
        for l in loglist:
            os.remove(l)
            os.remove(l[:-3] + "01.csv")
            try:
                os.remove(l[:-3] + "01.event")
            except:
                logging.warning("No .event file of " + l + " found.")
        return

    def _csv_iter(self, heads):
        figs = []
        for h in heads:
            analysed = plotter.CSV_log(
                h["tempFile"][:-3] + "01.csv", self.name, h, self.noise_bounds
            )
            # figs.append([analysed.fig_resp,analysed.fig_noise])
            if self.show != "Y":
                plt.cla()
                plt.clf()
        return figs

    def beheader(self, loglist):
        heads = []
        for i, bblog in enumerate(loglist):
            log = open(os.path.join(self.tmp_dir, bblog), "rb")
            lines = log.readlines()
            ### in case info is not provided by log, empty str is printed in plot
            headsdict = {
                "tempFile": "",
                "dynThrottle": "",
                "craftName": "",
                "fwType": "",
                "version": "",
                "date": "",
                "rcRate": "",
                "rcExpo": "",
                "rcYawExpo": "",
                "rcYawRate": "",
                "rates": "",
                "rollPID": "",
                "pitchPID": "",
                "yawPID": "",
                "deadBand": "",
                "yawDeadBand": "",
                "logNum": "",
                "tpa_breakpoint": "0",
                "minThrottle": "",
                "maxThrottle": "",
                "tpa_percent": "",
                "dTermSetPoint": "",
                "vbatComp": "",
                "gyro_lpf": "",
                "gyro_lowpass_type": "",
                "gyro_lowpass_hz": "",
                "gyro_notch_hz": "",
                "gyro_notch_cutoff": "",
                "dterm_filter_type": "",
                "dterm_lpf_hz": "",
                "yaw_lpf_hz": "",
                "dterm_notch_hz": "",
                "dterm_notch_cutoff": "",
                "debug_mode": "",
            }
            ### different versions of fw have different names for the same thing.
            translate_dic = {
                "dynThrPID:": "dynThrottle",
                "Craft name:": "craftName",
                "Firmware type:": "fwType",
                "Firmware revision:": "version",
                "Firmware date:": "fwDate",
                "rcRate:": "rcRate",
                "rc_rate:": "rcRate",
                "rcExpo:": "rcExpo",
                "rc_expo:": "rcExpo",
                "rcYawExpo:": "rcYawExpo",
                "rc_expo_yaw:": "rcYawExpo",
                "rcYawRate:": "rcYawRate",
                "rc_rate_yaw:": "rcYawRate",
                "rates:": "rates",
                "rollPID:": "rollPID",
                "pitchPID:": "pitchPID",
                "yawPID:": "yawPID",
                " deadband:": "deadBand",
                "yaw_deadband:": "yawDeadBand",
                "tpa_breakpoint:": "tpa_breakpoint",
                "minthrottle:": "minThrottle",
                "maxthrottle:": "maxThrottle",
                "dtermSetpointWeight:": "dTermSetPoint",
                "dterm_setpoint_weight:": "dTermSetPoint",
                "vbat_pid_compensation:": "vbatComp",
                "vbat_pid_gain:": "vbatComp",
                "gyro_lpf:": "gyro_lpf",
                "gyro_lowpass_type:": "gyro_lowpass_type",
                "gyro_lowpass_hz:": "gyro_lowpass_hz",
                "gyro_lpf_hz:": "gyro_lowpass_hz",
                "gyro_notch_hz:": "gyro_notch_hz",
                "gyro_notch_cutoff:": "gyro_notch_cutoff",
                "dterm_filter_type:": "dterm_filter_type",
                "dterm_lpf_hz:": "dterm_lpf_hz",
                "yaw_lpf_hz:": "yaw_lpf_hz",
                "dterm_notch_hz:": "dterm_notch_hz",
                "dterm_notch_cutoff:": "dterm_notch_cutoff",
                "debug_mode:": "debug_mode",
            }

            headsdict["tempFile"] = bblog
            headsdict["logNum"] = str(i)
            ### check for known keys and translate to useful ones.
            for raw_line in lines:
                l = raw_line.decode("latin-1")
                for k in translate_dic.keys():
                    if k in l:
                        val = l.split(":")[-1]
                        headsdict.update({translate_dic[k]: val[:-1]})

            heads.append(headsdict)
        return heads

    def decode(self, fpath):
        """Splits out one BBL per recorded session and converts each to CSV."""
        with open(fpath, "rb") as binary_log_view:
            content = binary_log_view.read()

        # The first line of the overall BBL file re-appears at the beginning
        # of each recorded session.
        try:
            first_newline_index = content.index(str("\n").encode("utf8"))
        except ValueError as e:
            raise ValueError(
                "No newline in %dB of log data from %r." % (len(content), fpath), e
            )
        firstline = content[: first_newline_index + 1]

        split = content.split(firstline)
        bbl_sessions = []
        for i in range(len(split)):
            path_root, path_ext = os.path.splitext(os.path.basename(fpath))
            temp_path = os.path.join(
                self.tmp_dir, "%s_temp%d%s" % (path_root, i, path_ext)
            )
            with open(temp_path, "wb") as newfile:
                newfile.write(firstline + split[i])
            bbl_sessions.append(temp_path)

        loglist = []
        for bbl_session in bbl_sessions:
            size_bytes = os.path.getsize(os.path.join(self.tmp_dir, bbl_session))
            if size_bytes > LOG_MIN_BYTES:
                try:
                    msg = subprocess.check_call(
                        [self.blackbox_decode_bin_path, bbl_session]
                    )
                    loglist.append(bbl_session)
                except:
                    logging.error(
                        "Error in Blackbox_decode of %r" % bbl_session, exc_info=True
                    )
            else:
                # There is often a small bogus session at the start of the file.
                logging.warning(
                    "Ignoring BBL session %r, %dB < %dB."
                    % (bbl_session, size_bytes, LOG_MIN_BYTES)
                )
                os.remove(bbl_session)
        return loglist

