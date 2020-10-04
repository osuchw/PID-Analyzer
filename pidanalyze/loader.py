import logging
import os
import subprocess

import numpy as np
from pandas import read_csv

LOG_MIN_BYTES = 500000


def deletejunk(loglist):
    for log in loglist:
        os.remove(log)
        os.remove(f"{log[:-3]}01.csv")
        try:
            os.remove(f"{log[:-3]}01.event")
        except:
            logging.warning("No .event file of %s found.", log)


def beheader(loglist, tmp_dir):
    heads = []
    for i, bblog in enumerate(loglist):
        log = open(os.path.join(tmp_dir, bblog), "rb")
        lines = log.readlines()
        ### in case info is not provided by log, empty str is printed in plot
        head = {
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
        translate_dict = {
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

        head["tempFile"] = bblog
        head["logNum"] = str(i)
        ### check for known keys and translate to useful ones.
        for raw_line in lines:
            ln = raw_line.decode("latin-1")
            for key in translate_dict:
                if key in ln:
                    val = ln.split(":")[-1]
                    head[translate_dict[key]] = val[:-1]

        heads.append(head)
    return heads


def decode(fpath, tmp_dir, blackbox_decode_bin_path):
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
        temp_path = os.path.join(tmp_dir, "%s_temp%d%s" % (path_root, i, path_ext))
        with open(temp_path, "wb") as newfile:
            newfile.write(firstline + split[i])
        bbl_sessions.append(temp_path)

    loglist = []
    for bbl_session in bbl_sessions:
        size_bytes = os.path.getsize(os.path.join(tmp_dir, bbl_session))
        if size_bytes > LOG_MIN_BYTES:
            try:
                msg = subprocess.check_call([blackbox_decode_bin_path, bbl_session])
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
    # keycheck for 'usecols' only reads usefull traces, uncommend if needed
    wanted = {
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
        #'accSmooth[0]', 'accSmooth[1]', 'accSmooth[2]',
        "debug[0]",
        "debug[1]",
        "debug[2]",
        "debug[3]",
        #'motor[0]', 'motor[1]', 'motor[2]', 'motor[3]',
        #'energyCumulative (mAh)', 'vbatLatest (V)', 'amperageLatest (A)'
    }
    dframe = read_csv(
        fpath,
        header=0,
        skipinitialspace=1,
        usecols=lambda k: k in wanted,
        dtype=np.float64,
    )
    data = {}
    data["time_us"] = dframe["time (us)"].values * 1e-6
    data["throttle"] = dframe["rcCommand[3]"].values

    for i in [0, 1, 2]:
        data[f"rcCommand{i}"] = dframe[f"rcCommand[{i}]"].values
        if f"debug[{i}]" in dframe:
            data[f"debug{i}"] = dframe[f"debug[{i}]"].values
        else:
            logging.warning("No debug[%s] trace found!", i)
            data[f"debug{i}"] = np.zeros_like(dframe[f"rcCommand[{i}]"].values)

        # get P trace (including case of missing trace)
        if f"axisP[{i}]" in dframe:
            data[f"PID loop in{i}"] = dframe[f"axisP[{i}]"].values
        else:
            logging.warning("No P[%s] trace found!", i)
            data[f"PID loop in{i}"] = np.zeros_like(dframe[f"rcCommand[{i}]"].values)

        if f"axisD[{i}]" in dframe:
            data[f"d_err{i}"] = dframe[f"axisD[{i}]"].values
        else:
            logging.warning("No D[%s] trace found!", i)
            data[f"d_err{i}"] = np.zeros_like(dframe[f"rcCommand[{i}]"].values)

        if f"axisI[{i}]" in dframe:
            data[f"I_term{i}"] = dframe[f"axisI[{i}]"].values
        else:
            if i < 2:
                logging.warning("No I[%s] trace found!", i)
            data[f"I_term{i}"] = np.zeros_like(dframe[f"rcCommand[{i}]"].values)

        data[f"PID sum{i}"] = (
            data[f"PID loop in{i}"] + data[f"I_term{i}"] + data[f"d_err{i}"]
        )
        if "gyroADC[0]" in dframe:
            data[f"gyroData{i}"] = dframe[f"gyroADC[{i}]"].values
        elif "gyroData[0]" in dframe:
            data[f"gyroData{i}"] = dframe[f"gyroData[{i}]"].values
        elif "ugyroADC[0]" in dframe:
            data[f"gyroData{i}"] = dframe[f"ugyroADC[{i}]"].values
        else:
            logging.warning("No gyro trace found!")

    return data


def find_traces(data, head):
    time = data["time_us"]
    throttle = (
        (data["throttle"] - 1000.0) / (float(head["maxThrottle"]) - 1000.0)
    ) * 100.0

    traces = []
    for i, name in enumerate(["roll", "pitch", "yaw"]):
        data["name"] = name
        data["time"] = time
        data["throttle"] = throttle
        data["p_err"] = data[f"PID loop in{i}"]
        data["rcinput"] = data[f"rcCommand{i}"]
        data["gyro"] = data[f"gyroData{i}"]
        data["PIDsum"] = data[f"PID sum{i}"]
        data["d_err"] = data[f"d_err{i}"]
        data["debug"] = data[f"debug{i}"]
        if "KISS" in head["fwType"]:
            data["P"] = 1.0
            head["tpa_percent"] = 0.0
        elif "Raceflight" in head["fwType"]:
            data["P"] = 1.0
            head["tpa_percent"] = 0.0
        else:
            data["P"] = float((head[data["name"] + "PID"]).split(",")[0])
            head["tpa_percent"] = (float(head["tpa_breakpoint"]) - 1000.0) / 10.0
        traces.append(data)
    return traces
