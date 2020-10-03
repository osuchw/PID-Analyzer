import logging
import os
import subprocess

import numpy as np
from pandas import read_csv

LOG_MIN_BYTES = 500000


class BB_log:
    def __init__(self, log_file_path, name, blackbox_decode):
        self.blackbox_decode_bin_path = blackbox_decode
        self.tmp_dir = os.path.join(os.path.dirname(log_file_path), name)
        if not os.path.isdir(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def deletejunk(self, loglist):
        for l in loglist:
            os.remove(l)
            os.remove(l[:-3] + "01.csv")
            try:
                os.remove(l[:-3] + "01.event")
            except:
                logging.warning("No .event file of " + l + " found.")
        return

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


def readcsv(fpath):
    datdic = {}
    ### keycheck for 'usecols' only reads usefull traces, uncommend if needed
    wanted = [
        "time (us)",
        "rcCommand[0]",
        "rcCommand[1]",
        "rcCommand[2]",
        "rcCommand[3]",
        "axisP[0]",
        "axisP[1]",
        "axisP[2]",
        "axisI[0]",
        "axisI[1]",
        "axisI[2]",
        "axisD[0]",
        "axisD[1]",
        "axisD[2]",
        "gyroADC[0]",
        "gyroADC[1]",
        "gyroADC[2]",
        "gyroData[0]",
        "gyroData[1]",
        "gyroData[2]",
        "ugyroADC[0]",
        "ugyroADC[1]",
        "ugyroADC[2]",
        #'accSmooth[0]','accSmooth[1]', 'accSmooth[2]',
        "debug[0]",
        "debug[1]",
        "debug[2]",
        "debug[3]",
        #'motor[0]', 'motor[1]', 'motor[2]', 'motor[3]',
        #'energyCumulative (mAh)','vbatLatest (V)', 'amperageLatest (A)'
    ]
    data = read_csv(
        fpath,
        header=0,
        skipinitialspace=1,
        usecols=lambda k: k in wanted,
        dtype=np.float64,
    )
    datdic.update({"time_us": data["time (us)"].values * 1e-6})
    datdic.update({"throttle": data["rcCommand[3]"].values})

    for i in ["0", "1", "2"]:
        datdic.update({"rcCommand" + i: data["rcCommand[" + i + "]"].values})
        # datdic.update({'PID loop in' + i: data['axisP[' + i + ']'].values})
        try:
            datdic.update({"debug" + i: data["debug[" + i + "]"].values})
        except:
            logging.warning("No debug[" + str(i) + "] trace found!")
            datdic.update(
                {"debug" + i: np.zeros_like(data["rcCommand[" + i + "]"].values)}
            )

        # get P trace (including case of missing trace)
        try:
            datdic.update({"PID loop in" + i: data["axisP[" + i + "]"].values})
        except:
            logging.warning("No P[" + str(i) + "] trace found!")
            datdic.update(
                {
                    "PID loop in"
                    + i: np.zeros_like(data["rcCommand[" + i + "]"].values)
                }
            )

        try:
            datdic.update({"d_err" + i: data["axisD[" + i + "]"].values})
        except:
            logging.warning("No D[" + str(i) + "] trace found!")
            datdic.update(
                {"d_err" + i: np.zeros_like(data["rcCommand[" + i + "]"].values)}
            )

        try:
            datdic.update({"I_term" + i: data["axisI[" + i + "]"].values})
        except:
            if i < 2:
                logging.warning("No I[" + str(i) + "] trace found!")
            datdic.update(
                {"I_term" + i: np.zeros_like(data["rcCommand[" + i + "]"].values)}
            )

        datdic.update(
            {
                "PID sum"
                + i: datdic["PID loop in" + i]
                + datdic["I_term" + i]
                + datdic["d_err" + i]
            }
        )
        if "gyroADC[0]" in data.keys():
            datdic.update({"gyroData" + i: data["gyroADC[" + i + "]"].values})
        elif "gyroData[0]" in data.keys():
            datdic.update({"gyroData" + i: data["gyroData[" + i + "]"].values})
        elif "ugyroADC[0]" in data.keys():
            datdic.update({"gyroData" + i: data["ugyroADC[" + i + "]"].values})
        else:
            logging.warning("No gyro trace found!")
    return datdic


def find_traces(dat, headdict):
    time = dat["time_us"]
    throttle = dat["throttle"]

    throt = (
        (throttle - 1000.0) / (float(headdict["maxThrottle"]) - 1000.0)
    ) * 100.0

    traces = [{"name": "roll"}, {"name": "pitch"}, {"name": "yaw"}]

    for i, dic in enumerate(traces):
        dic.update({"time": time})
        dic.update({"p_err": dat["PID loop in" + str(i)]})
        dic.update({"rcinput": dat["rcCommand" + str(i)]})
        dic.update({"gyro": dat["gyroData" + str(i)]})
        dic.update({"PIDsum": dat["PID sum" + str(i)]})
        dic.update({"d_err": dat["d_err" + str(i)]})
        dic.update({"debug": dat["debug" + str(i)]})
        if "KISS" in headdict["fwType"]:
            dic.update({"P": 1.0})
            headdict.update({"tpa_percent": 0.0})
        elif "Raceflight" in headdict["fwType"]:
            dic.update({"P": 1.0})
            headdict.update({"tpa_percent": 0.0})

        else:
            dic.update(
                {"P": float((headdict[dic["name"] + "PID"]).split(",")[0])}
            )
            headdict.update(
                {
                    "tpa_percent": (float(headdict["tpa_breakpoint"]) - 1000.0)
                    / 10.0
                }
            )

        dic.update({"throttle": throt})

    return traces