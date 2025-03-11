from scipy import signal, optimize
import numpy as np
import DataHandling as DH
import matplotlib.pyplot as plt

def waveletTimeFrequency(data, freq, ma=1, w=6, fs=100):
    widths = w * fs / (2 * freq * np.pi)
    cwtm = signal.cwt(data, signal.morlet2, widths, w=w)
    power = np.abs(cwtm)
    if ma > 1:
        for i in range(len(data)):
            if i < ma:
                power[:,i] = np.mean(power[:,:i+ma],axis=1)
            elif i+ma >= len(data):
                power[:,i] = np.mean(power[:,i-ma:],axis=1)
            else:
                power[:,i] = np.mean(power[:,i-ma:i+ma],axis=1)
    return dict({"Time": np.array(range(len(data)))/fs,"Frequency": freq, "Power": power, "logPower": 10*np.log10(power)})

def defaultSpectrogram(data, window=2.0, overlap=1.0, frequency_resolution=0.5, fs=100):
    configuration = {"Window": window, "Overlap": overlap}
    window = int(window * fs)
    overlap = int(overlap * fs)
    NFFT = int(fs / frequency_resolution)
    frequency, time, spectrum = signal.spectrogram(data, window="hamming", nperseg=window, noverlap=overlap, nfft=NFFT, fs=fs)
    return dict({"Time": time, "Frequency": frequency, "Power": np.abs(spectrum), "logPower": 10*np.log10(np.abs(spectrum)), "Config": configuration})

def removeCardiacComponent(raw, filterMethod="Fixed Peak Find"):
    stream = raw['Y']
    fs = 250
    #Filtrar bandpass butter
    [b,a] = signal.butter(5, np.array([1,100])*2/fs, 'bp', output='ba')
    filtered = signal.filtfilt(b, a, stream)
    buttered = filtered.copy()

    #filterMethod = "Kurtosis"
    PredictedSignal = signal.wiener(filtered, mysize=125)
    filtered -= PredictedSignal

    if filterMethod == "Fixed Peak Find":
        # Cardiac Filter
        posPeaks,_ = signal.find_peaks(filtered, prominence=[10,200], distance=fs*0.5)
        PosCardiacVariability = np.std(np.diff(posPeaks))
        negPeaks,_ = signal.find_peaks(-filtered, prominence=[10,200], distance=fs*0.5)
        NegCardiacVariability = np.std(np.diff(negPeaks))

        if PosCardiacVariability < NegCardiacVariability:
            peaks = posPeaks
        else:
            peaks = negPeaks
        CardiacRate = int(np.mean(np.diff(peaks)))

        PrePeak = int(CardiacRate*0.25)
        PostPeak = int(CardiacRate*0.65)
        EKGMatrix = np.zeros((len(peaks)-2,PrePeak+PostPeak))
        for j in range(1,len(peaks)-1):
            if peaks[j]+PostPeak < len(filtered) and peaks[j]-PrePeak > 0:
                EKGMatrix[j-1,:] = filtered[peaks[j]-PrePeak:peaks[j]+PostPeak]

        EKGTemplate = np.mean(EKGMatrix,axis=0)
        EKGTemplate = EKGTemplate / (np.max(EKGTemplate)-np.min(EKGTemplate))

        def EKGTemplateFunc(xdata, amplitude, offset):
            return EKGTemplate * amplitude + offset

        for j in range(len(peaks)):
            if peaks[j]-PrePeak < 0:
                pass
            elif peaks[j]+PostPeak >= len(filtered) :
                pass
            else:
                sliceSelection = np.arange(peaks[j]-PrePeak,peaks[j]+PostPeak)
                params, covmat = optimize.curve_fit(EKGTemplateFunc, sliceSelection, filtered[sliceSelection])
                filtered[sliceSelection] = filtered[sliceSelection] - EKGTemplateFunc(sliceSelection, *params)
                ecg = EKGTemplateFunc(sliceSelection, *params)

        #wavelet = waveletTimeFrequency(filtered, freq=np.arange(0.5,100.5,0.5), ma=int(fs/2), fs=fs)
        #sfft = defaultSpectrogram(stream, window=1.0, overlap=0.5, frequency_resolution=0.5, fs=fs)

        return filtered, ecg, buttered, peaks
    
file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
stream = DH.getSignals(Data, 'Streaming')[0]

filtered, ecg, buttered, peaks = removeCardiacComponent(stream)

threshold = []
for p in peaks:
    threshold.append(stream['Y'][p])
#threshold = [np.abs(v) for v in threshold]

line = np.min(threshold)

plt.figure()

#plt.plot(stream['X'],stream['Y'],label='Raw')

plt.plot(stream['X'],buttered,label='Butter Filter')
plt.plot(stream['X'],filtered,label='No Cardiac Component', linestyle = '--')
plt.plot(np.arange(0,len(ecg)),ecg, label = 'ECG')
plt.hlines(y = [line, - line], xmin = 0, xmax = len(stream['X'])/250, label = 'Threshold', color = 'red', linestyle = '--')

plt.legend()
plt.show()

print('end')