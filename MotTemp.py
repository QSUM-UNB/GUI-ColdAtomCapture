import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
from lmfit.models import QuadraticModel, LinearModel
import lmfit as lm
from PyQt6.QtGui import QTextDocument
import time
import os

def Gaussian(x, amp, cen, wid, off):
    """1-d Gaussian: gaussian(x, amp, cen, wid, off)"""
    return amp * np.exp(-((x-cen)/wid)**2) + off

def Hyperbolic(x, s0, sv):
    return np.sqrt(s0**2 + (sv**2 * x**2))

def main(baseDir, numImages, window, timeSplit):
    for a in window.analysisWidget.axes:
        for e in a:
            e.cla()
    fileArr = []
    #backArr = []
    timeArr = []
    for e in range(numImages):
        newFile = f"{baseDir}CloudDetection_TOF-{timeSplit[e]}ms.tiff"
        if os.path.exists(newFile):
            fileArr.append(f"{baseDir}CloudDetection_TOF-{timeSplit[e]}ms.tiff")
            timeArr.append(timeSplit[e])
        else:
            numImages -= 1
        #backArr.append("../MotTemp/Pics5/2024-06-24_CloudDetection_TOF_background_01.tiff")
    plt_x = [None]*len(fileArr)
    plt_y = [None]*len(fileArr)
    x_pos = [None]*len(fileArr)
    y_pos = [None]*len(fileArr)
    amp = [None]*len(fileArr)
    centre = [None]*len(fileArr)
    sigma = [None]*len(fileArr)
    yamp = [None]*len(fileArr)
    ycentre = [None]*len(fileArr)
    ysigma = [None]*len(fileArr)
    for i in range(0, len(fileArr)):
        window.statusbar.showMessage(f"Processing image {i+1} of {numImages}...")
        plt_x[i], plt_y[i], x_pos[i], y_pos[i], amp[i], centre[i], sigma[i], yamp[i], ycentre[i], ysigma[i] = findStdDev(fileArr[i], window)

    if len(plt_x) == 0:
        window.statusbar.showMessage("ERROR: No images were loaded")
        if window.mode == 0:
            window.tofStartBox.setEnabled(True)
            window.tofEndBox.setEnabled(True)
            window.tofSplitBox.setEnabled(True)
        window.camThread = None
    
    window.statusbar.showMessage("Fitting data...")
    
    axis_pts_ms = [x/1000 for x in timeArr]
    runningString = ""

    mod = QuadraticModel()
    pars = mod.guess(np.array(centre), x=np.array(axis_pts_ms))
    out = mod.fit(np.array(centre), pars, x=np.array(axis_pts_ms))
    runningString += f"X-axis Centre Results:\na: {out.best_values['a']}\nb: {out.best_values['b']}\nc: {out.best_values['c']}\n\n"
    window.analysisWidget.axes[1][0].plot(axis_pts_ms, out.best_fit)
    window.analysisWidget.axes[1][0].scatter(axis_pts_ms, centre, c='tab:orange')
    print(out.fit_report(min_correl=0.25))

    mod = QuadraticModel()
    pars = mod.guess(np.array(ycentre), x=np.array(axis_pts_ms))
    out = mod.fit(np.array(ycentre), pars, x=np.array(axis_pts_ms))
    gravity = out.best_values['a'] * 2
    runningString += f"Y-axis Centre Results:\ng: {gravity}m/s^2\nv_y: {out.best_values['b']}m/s\ny_i: {out.best_values['c']}m\n\n"
    window.analysisWidget.axes[1][1].plot(axis_pts_ms, out.best_fit)
    window.analysisWidget.axes[1][1].scatter(axis_pts_ms, ycentre, c='tab:orange')
    print(out.fit_report(min_correl=0.25))

    mod = LinearModel()
    pars = mod.guess(np.array(sigma), x=np.array(axis_pts_ms))
    out = mod.fit(np.array(sigma), pars, x=np.array(axis_pts_ms))
    temp = 0.5 * ((1.44 * math.pow(10,-25))/(1.38 * math.pow(10,-23))) * math.pow(out.best_values['slope'], 2)
    print(out.fit_report(min_correl=0.25))

    linear_guess = out.best_values['slope']

    mod = lm.Model(Hyperbolic)
    p_s0 = lm.Parameter(name='s0', value=sigma[0])
    p_sv = lm.Parameter(name='sv', value=linear_guess)
    params = lm.Parameters()
    params.add_many(p_s0, p_sv)
    out = mod.fit(np.array(sigma), params, x=np.array(axis_pts_ms))
    temp = 0.5 * ((1.44 * math.pow(10,-25))/(1.38 * math.pow(10,-23))) * math.pow(out.best_values['sv'], 2)
    runningString += f"X-Axis Sigma Results:\ns0: {out.best_values['s0']}m/s\nsv: {out.best_values['sv']}m\n Temperature: {temp}K\n\n"
    window.analysisWidget.axes[2][0].plot(axis_pts_ms, out.best_fit)
    window.analysisWidget.axes[2][0].scatter(axis_pts_ms, sigma, c='tab:orange')
    print(out.fit_report(min_correl=0.25))

    mod = lm.Model(Hyperbolic)
    p_s0 = lm.Parameter(name='s0', value=ysigma[0])
    p_sv = lm.Parameter(name='sv', value=linear_guess)
    params = lm.Parameters()
    params.add_many(p_s0, p_sv)
    out = mod.fit(np.array(ysigma), params, x=np.array(axis_pts_ms))
    temp = 0.5 * ((1.44 * math.pow(10,-25))/(1.38 * math.pow(10,-23))) * math.pow(out.best_values['sv'], 2)
    runningString += f"Y-Axis Sigma Results:\ns0: {out.best_values['s0']}\nsv: {out.best_values['sv']}\nTemperature: {temp}K"
    window.analysisWidget.axes[2][1].plot(axis_pts_ms, out.best_fit)
    window.analysisWidget.axes[2][1].scatter(axis_pts_ms, ysigma, c='tab:orange')
    print(out.fit_report(min_correl=0.25))

    text = QTextDocument()
    text.setPlainText(runningString)
    window.fitText.setDocument(text)

    window.analysisWidget.axes[0][0].scatter(axis_pts_ms, amp, c='tab:orange')
    window.analysisWidget.axes[0][1].scatter(axis_pts_ms, yamp, c='tab:orange')

    window.analysisWidget.axes[0][0].title.set_text("X-Axis Amplitude")
    window.analysisWidget.axes[0][1].title.set_text("Y-Axis Amplitude")
    window.analysisWidget.axes[1][0].title.set_text("X-Axis Centre")
    window.analysisWidget.axes[1][1].title.set_text("Y-Axis Centre")
    window.analysisWidget.axes[2][0].title.set_text("X-Axis Sigma")
    window.analysisWidget.axes[2][1].title.set_text("Y-Axis Sigma")
    window.analysisWidget.axes[2][0].set_xlabel("Time (s)")
    window.analysisWidget.axes[2][1].set_xlabel("Time (s)")
    window.analysisWidget.axes[0][0].set_ylabel("Pixel Intensity")
    window.analysisWidget.axes[1][0].set_ylabel("Position (m)")
    window.analysisWidget.axes[2][0].set_ylabel("Position (m)")
    window.analysisWidget.draw()
    window.statusbar.showMessage("Processing finished.")
    if window.mode == 0:
        window.tofStartBox.setEnabled(True)
        window.tofEndBox.setEnabled(True)
        window.tofSplitBox.setEnabled(True)
    window.camThread = None

def getIntegratedBins(image:np.ndarray) -> tuple[list[int],list[int]]:
    binx = []
    biny = []
    for i in range(0,len(image)):
        intensity = 0
        for j in range(0, len(image[0])):
            intensity += image[i][j]
        biny.append(intensity)

    for j in range(0, len(image[0])):
        intensity = 0
        for i in range(0, len(image)):
            intensity += image[i][j]
        binx.append(intensity)

    return (binx, biny)

def get1DArray(image:np.ndarray, peakX:int, peakY:int) -> tuple[list[int],list[int]]:
    x1d = []
    y1d = []
    for j in range(0, len(image[peakY])):
        x1d.append(image[peakY][j])
    for i in range(0, len(image)):
        y1d.append(image[i][peakX])
    return (x1d, y1d)

def get1DSum(x1d:list, y1d:list) -> tuple[int, int]:
    xsum = 0
    ysum = 0
    for e in x1d:
        xsum += e
    for e in y1d:
        ysum += e
    return (xsum, ysum)

def getProbability(x1d:list, y1d:list, xsum:int, ysum:int) -> tuple[list[float],list[float]]:
    px = []
    py = []
    for e in x1d:
        px.append(e/xsum)
    for e in y1d:
        py.append(e/ysum)
    return (px, py)

def getMu(px:list, py:list) -> tuple[float, float]:
    mux = 0.
    muy = 0.
    for i in range(len(px)):
        mux += px[i] * i
    for i in range(len(py)):
        muy += py[i] * i
    return (mux, muy)

def getVariance(px, py, mux, muy) -> tuple[float]:
    varx = 0.
    vary = 0.
    for i in range(len(px)):
        varx += px[i] * (i - mux)**2
    for i in range(len(py)):
        vary += py[i] * (i - muy)**2
    return (varx, vary)

def getROI(image:np.ndarray, stdx:int, stdy:int, peakX:int, peakY:int, sigmaFactor:int) -> tuple[list[int], list[int]]:
    roi_x = []
    roi_y = []
    for j in range(max(0, math.floor(peakX - (stdx*sigmaFactor))), min(len(image[peakY]), math.floor(peakX + (stdx*sigmaFactor)))):
        roi_x.append(image[peakY][j])
    for i in range(max(0, math.floor(peakY - (stdy*sigmaFactor))), min(len(image), math.floor(peakY + (stdy*sigmaFactor))+1)):
        roi_y.append(image[i][peakX])
    return (roi_x, roi_y)

def getManualROI(image:np.ndarray, corners:list[tuple[int,int],tuple[int,int]], peakX:int, peakY:int) -> tuple[list[int],list[int]]:
    x1, y1 = corners[0]
    x2, y2 = corners[1]
    
    roi_x = []
    roi_y = []
    for j in range(x1, x2+1):
        roi_x.append(image[peakY][j])
    for i in range(y1, y2+1):
        roi_y.append(image[i][peakX])

    return (roi_x, roi_y)

def getStdDev(image:np.ndarray) -> tuple[float,float]:
    binx, biny = getIntegratedBins(image)
    peakX = binx.index(max(binx))
    peakY = biny.index(max(biny))
    x1d, y1d = get1DArray(image, peakX, peakY)
    return getROIStdDev(x1d, y1d)

def getROIStdDev(roi_x:list, roi_y:list) -> tuple[float,float]:
    xsum, ysum = get1DSum(roi_x, roi_y)
    px, py = getProbability(roi_x, roi_y, xsum, ysum)
    mux, muy = getMu(px, py)
    varx, vary = getVariance(px, py, mux, muy)
    stdx = math.sqrt(varx)
    stdy = math.sqrt(vary)
    return (stdx, stdy)

def runSingleImage(file, window) -> None:
    findStdDev(file, window)
    window.camThread = None
    window.statusbar.showMessage("Processing finished.")
    return
    
def findStdDev(file, window):
    image = cv2.imread(file, flags=cv2.IMREAD_ANYDEPTH)
    if type(image) == type(None):
        window.statusbar.showMessage("Cannot find file. Skipping...")
        time.sleep(3)
        return None
    image = np.asarray(image, dtype=np.float64)
    binx, biny = getIntegratedBins(image)
    peakX = binx.index(max(binx))
    peakY = biny.index(max(biny))
    if window.isAuto:
        stdx, stdy = getStdDev(image)
        stdx = math.floor(stdx)
        stdy = math.floor(stdy)
        sigmaFactor = window.sigFactor
        roi_x, roi_y = getROI(image, stdx, stdy, peakX, peakY, sigmaFactor)
        for j in range(max(0, math.floor(peakX - (stdx*sigmaFactor))), min(len(image[peakY]), math.floor(peakX + (stdx*sigmaFactor)))):
            image[max(0, peakY-(stdy*sigmaFactor))][j] = 65535
            image[min(len(image)-1, peakY+(stdy*sigmaFactor))][j] = 65535
        for i in range(max(0, math.floor(peakY - (stdy*sigmaFactor))), min(len(image), math.floor(peakY + (stdy*sigmaFactor))+1)):
            image[i][max(0, peakX-(stdx*sigmaFactor))] = 65535
            image[i][min(len(image[i])-1, peakX+(stdx*sigmaFactor))] = 65535
        x_pos = list(range(max(0, math.floor(peakX - (stdx*sigmaFactor))), min(len(image[0]), math.floor(peakX + (stdx*sigmaFactor)))))
        y_pos = list(range(max(0, math.floor(peakY - (stdy*sigmaFactor))), min(len(image), math.floor(peakY + (stdy*sigmaFactor))+1)))
    else:
        roi_x, roi_y = getManualROI(image, window.corners, peakX, peakY)
        x1, y1 = window.corners[0]
        x2, y2 = window.corners[1]
        for j in range(x1, x2+1):
            image[y1][j] = 65535
            image[y2][j] = 65535
        for i in range(y1, y2+1):
            image[i][x1] = 65535
            image[i][x2] = 65535
        x_pos = list(range(x1,x2+1))
        y_pos = list(range(y1,y2+1))

    np_x = np.asarray(roi_x)
    np_y = np.asarray(roi_y)
    min_x = list(np_x - min(roi_x))
    min_y = list(np_y - min(roi_y))
    std_plt_x, std_plt_y = getROIStdDev(min_x, min_y)
    mod = lm.Model(Gaussian)
    peak = roi_x.index(max(roi_x))
    p_amp = lm.Parameter(name='amp', value=roi_x[peak]-min(roi_x))
    p_cen = lm.Parameter(name='cen', value=(x_pos[peak]/window.pixelRatio)/1000)
    p_wid = lm.Parameter(name='wid', value=(std_plt_x/window.pixelRatio)/1000)
    p_off = lm.Parameter(name='off', value=min(roi_x))
    params = lm.Parameters()
    params.add_many(p_amp, p_cen, p_wid, p_off)
    out = mod.fit(np.array(roi_x), params, x=np.array([(x/window.pixelRatio)/1000 for x in x_pos]))
    window.camWidget.axes[1].plot(x_pos, roi_x, marker='o', color='tab:orange', linestyle='', markersize=4)
    window.camWidget.axes[1].plot(x_pos, out.best_fit)
    vals = out.best_values
    amp = vals['amp']
    centre = vals['cen']
    sigma = vals['wid']
    mod = lm.Model(Gaussian)
    peak = roi_y.index(max(roi_y))
    p_amp = lm.Parameter(name='amp', value=roi_y[peak]-min(roi_y))
    p_cen = lm.Parameter(name='cen', value=(y_pos[peak]/window.pixelRatio)/1000)
    p_wid = lm.Parameter(name='wid', value=(std_plt_y/window.pixelRatio)/1000)
    p_off = lm.Parameter(name='off', value=min(roi_y))
    params = lm.Parameters()
    params.add_many(p_amp, p_cen, p_wid, p_off)
    out = mod.fit(np.array(roi_y), params, x=np.array([(x/window.pixelRatio)/1000 for x in y_pos]))
    window.camWidget.axes[2].plot(roi_y, y_pos, marker='o', color='tab:orange', linestyle='', markersize=4)
    window.camWidget.axes[2].plot(out.best_fit, y_pos)
    vals = out.best_values
    yamp = vals['amp']
    ycentre = vals['cen']
    ysigma = vals['wid']
    for i in range(len(image)):
        image[i][math.floor(centre*1000*window.pixelRatio)] = 65535
    for j in range(len(image[0])):
        image[math.floor(ycentre*1000*window.pixelRatio)][j] = 65535
    window.camWidget.axes[0].imshow(image, cmap="gray")
    window.camWidget.axes[2].invert_yaxis()
    window.camWidget.axes[0].title.set_text("Camera View")
    window.camWidget.axes[1].title.set_text("X-Axis Profile")
    window.camWidget.axes[2].title.set_text("Y-Axis Profile")
    window.camWidget.draw()
    window.camWidget.axes[0].cla()
    window.camWidget.axes[1].cla()
    window.camWidget.axes[2].cla()
    time.sleep(window.delay)
    
    return (roi_x, roi_y, x_pos, y_pos, amp, centre, sigma, yamp, ycentre, ysigma)


if __name__ == "__main__":
    exit(0)