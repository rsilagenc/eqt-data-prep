import matplotlib
matplotlib.rcParams["pcolor.shading"] = "auto"

from obspy import read
from pathlib import Path

from EQTransformer.core.mseed_predictor import mseed_predictor

mseed_predictor(input_dir='/home/wsl-ubuntu/event_windows_mseed/event_0002_20240214T075313_M4.0',
                input_model='/home/wsl-ubuntu/EqT_original_model.h5',
                stations_json='station_list.json',
                output_dir='detection_results',
                detection_threshold=0.2,
                P_threshold=0.1,
                S_threshold=0.1,
                number_of_plots=10,
                plot_mode='time_frequency',
                batch_size=500,
                overlap=0.3)
