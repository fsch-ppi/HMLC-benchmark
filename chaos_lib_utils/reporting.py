"""
This module contains functions for generating reports and plots for the chaos experiments
"""
import pandas as pd
import os 
import numpy as np
import matplotlib.pyplot as plt 
from scipy.signal import find_peaks
from chaos_lib_utils.constants import LOG_FOLDER
from matplotlib.lines import Line2D


def read_csv(filename: str) -> pd.DataFrame:
    """
    This function reads a filename from the run folder and returns a pandas dataframe
    
    Parameters:
    filename: A string representing the filename
    """
    filename = os.path.join(os.getcwd(), LOG_FOLDER, filename)
    df = pd.read_csv(filename)
    return df

def remove_max_outliers_quantile(df: pd.DataFrame, column: str, quantile: float) -> pd.DataFrame:
    """
    This function removes the max outliers from a dataframe column (using quantiles)
    
    Parameters:
    df: A pandas dataframe
    column: A string representing the column name
    quantile: A float representing the quantile
    
    Returns:
    df: A pandas with only the quantile% smallest values
    """
    max_value = df[column].quantile(quantile)
    df[column] = np.where(df[column] > max_value, max_value, df[column])
    return df

def identify_chaos_events_derivative(df: pd.DataFrame, column: str, threshold: float) -> pd.DataFrame:
    """
    Identify chaos events using the difference (first derivative) method.
    
    Parameters:
    df: A pandas dataframe
    column: string (column name)
    threshold: A float representing the theshold for the acceptable difference
    
    Returns:
    df: pd.DataFrame with a new column 'Chaos' indicating chaos events
    """
    df['Difference'] = df[column].diff(periods=4).abs()
    chaos_events = df['Difference'] > threshold
    df['Chaos'] = 0
    df.loc[chaos_events, 'Chaos'] = 1
    df.drop(columns=['Difference'], inplace=True)
    
    # Ensure continuity of chaos events
    # If the previous value is a chaos event and the current values is above the threshold, it is a chaos event
    df['Chaos'] = df['Chaos'].rolling(window=2).max()
    df['Chaos'].fillna(0, inplace=True)
    return df

def identify_chaos_events_quantiles(df: pd.DataFrame, column: str, upper_quantile: float) -> pd.DataFrame:
    """
    Identify chaos events using quantiles.
    If the value is larger than the upper_quantile, it is considered a chaos event.
    
    This metric ensures continuity of the chaos events.
    
    Parameters:
    df: A pandas dataframe
    column: string (column name)
    upper_quantile: A float representing the quantile
    """
    max_value = df[column].quantile(upper_quantile)
    chaos_events = df[column] > max_value
    df['Chaos'] = 0
    df.loc[chaos_events, 'Chaos'] = 1
    
    # Ensure continuity of chaos events
    # If the previous value is a chaos event and the current values is above the threshold, it is a chaos event
    df['Chaos'] = df['Chaos'].rolling(window=2).max()
    df['Chaos'].fillna(0, inplace=True)
    return df

def identify_chaos_events_moving_average(df: pd.DataFrame, column: str, window_size: int, k: float=2) -> pd.DataFrame:
    """
    Identify chaos events using a moving average and standard deviation.
    If the value is larger than the moving average plus k times the standard deviation, it is considered a chaos event.
    
    Parameters:
    df: A pandas dataframe
    column: string (column name to monitor for chaos events)
    window_size: int (size of the moving window for average and standard deviation calculation)
    k: float (multiplier for the standard deviation to define the threshold)
    
    Returns:
    df: pd.DataFrame with a new column 'Chaos' indicating chaos events
    """
    
    # Calculate the rolling average rolling stdev
    df['rolling_avg'] = df[column].rolling(window=window_size, min_periods=1).mean()
    df['rolling_std'] = df[column].rolling(window=window_size, min_periods=1).std()

    # threshold for chaos events	
    df['threshold'] = df['rolling_avg'] + k * df['rolling_std']
    
    # Identify chaos events
    chaos_events = df[column] > df['threshold']
    df['Chaos'] = 0
    df.loc[chaos_events, 'Chaos'] = 1
    
    # Ensure continuity of chaos events
    #df['Chaos'] = df['Chaos'].rolling(window=2).max()
    #df['Chaos'].fillna(0, inplace=True)
    
    df = df.drop(columns=['rolling_avg', 'rolling_std', 'threshold'])
    return df

def time_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function normalizes the time column of a dataframe
    It expects time to be as a unix timestamp
    
    It will take the first unix timestamp value and subtract it from all other timestamps
    Parameters:
    df: A pandas dataframe
    
    Returns:
    df: A pandas dataframe with normalized time column
    """
    df['Time'] = df['Time'] - df['Time'].iloc[0]
    return df

from typing import List, Tuple

def find_number_of_chaos_groups(df: pd.DataFrame) -> Tuple[int, List[List[int]]]:
    """
    This function finds the number of chaos groups in a dataframe:
    A group is a sequence of chaos events that are continuous

    Note:
    Continous is not refering to continous time - since this can be flawed in the data.
    It is refering to indecies of the dataframe - which is best effort.
    
    Parameters:
    df: A pandas dataframe
    
    Returns:
    number_of_groups: An integer representing the number of chaos groups
    """
    number_of_chaos_groups = 0
    chaos_groups = []
    
    prev = False
    for index, value in enumerate(df['Chaos']):
        if value == 1 and prev == False:
            number_of_chaos_groups += 1
            chaos_groups.append([index])
        
        # Chaos events end or the last value is a chaos event
        if value == 0 and prev == True or index == len(df)-1 and value == 1:
            chaos_groups[-1].append(index-1)
        prev = value
    
    return number_of_chaos_groups, chaos_groups

# Plot the data as a line graph
def plot_chaos_events(df: pd.DataFrame, chaos_events: list[list[int]], title : str = "Chaos Events", figsize: Tuple[int, int]=(15, 5), legend : bool = False) -> None:
    """
    This function plots the chaos experiment on a line graph
    It returns a plot, with the start and end of the chaos events marked
    The start is marked with a red horizontal line and the end is marked with a green horizontal line
    
    Parameters:
    df: A pandas dataframe
    chaos_events: A list of lists containing lists with the start and end indices
    """
    # Plot the data as a line graph with different colors for chaos events
    plt.figure(figsize=figsize)
    plt.plot(df['Time'], df['Value'], color='blue')
    
    # Add chaos event lines
    for event in chaos_events:
        plt.axvline(x=df['Time'].iloc[event[0]], color='red', linestyle='--')
        plt.axvline(x=df['Time'].iloc[event[1]], color='green', linestyle='--')
    
    # Custom legend
    if legend:
        legend = [
            {"label": "Start of Detected Chaos Events", "color": "red", "linestyle": "--"},
            {"label": "End of Detected Chaos Events", "color": "green", "linestyle": "--"},
            {"label": "Data", "color": "blue"},
            ]
        # legend lines
        legend_lines = [
            Line2D(
                [0], [0], color=item["color"], linestyle=item.get("linestyle", "-"), label=item["label"]
            )
            for item in legend
        ]
        # centering in the top middle
        plt.legend(handles=legend_lines, loc='upper center', bbox_to_anchor=(0.5, 1.085), ncol=len(legend), facecolor='white',)
    
    plt.xlabel('Time in Seconds')
    plt.ylabel('Consumer Group Lag')
    plt.title(title)
    plt.show()
    
def plot_time_series(df: pd.DataFrame, label: str=None) -> None:
    plt.figure(figsize=(15, 5))
    plt.plot(df['Time'], df['Value'], color='blue')
    plt.xlabel('Time')
    plt.ylabel('Value')
    if label:
        plt.title(label)
    plt.show()
    
def get_duration(df: pd.DataFrame, chaos_event: list[int, int]) -> float:
    """
    This function returns the duration of a chaos event represented by
    [start, end] in the dataframe. The Time column is used to calculate the duration.
    """
    duration = df['Time'].iloc[chaos_event[1]] - df['Time'].iloc[chaos_event[0]]
    return duration

def allign_chaos_evnets(dataframes : list[pd.DataFrame], chaos_events_list : list[list[list[int,int]]]) -> list[pd.DataFrame]:
    """
    This function alligns all data frames so they have the same time before the first chaos event.
    It then returns the alligned dataframes (with normalized time columns) and the new chaos events index list.
    
    Parameters:
    dataframes: list[pd.DataFrame]: A list of pandas dataframes
    chaos_events_list: list[list[int,int]]: A list of lists containing the start and end indices of chaos events
    
    Returns:
    alligned_dataframes: list[pd.DataFrame]: dataframes alligned to the first chaos event
    alligned_chaos_events: list[list[int,int]]: chaos events alligned to the first chaos event
    """
    # Preconditions, otherwise the function will not work sensibly
    assert len(dataframes) == len(chaos_events_list), "Dataframes and chaos events list must have the same length"
    # This is not strictly needed but a good sanity check to not make methodical errors!
    for chaos_events in chaos_events_list:
        assert len(chaos_events) == len(chaos_events_list[0]), "All chaos events lists must have the same length"
        
        
    # Find the first chaos event in all dataframes
    first_chaos_events = []
    differences = []
    for i, all_chaos_events in enumerate(chaos_events_list):
        assert type(all_chaos_events[0][0]) == list, "Chaos events must be a list of lists"
        assert len(all_chaos_events[0][0]) == 2, "Chaos events must be a list of lists with two elements"
        assert type(all_chaos_events[0][0][0]) == int and type(all_chaos_events[0][0][1] == int), "Chaos events must be a list of lists with two integers"
        first_chaos_events.append(all_chaos_events[0][0])    
    # Compute the time difference between the first time value and the first chaos event
    for i, df in enumerate(dataframes):
        # normalize time, then compute the time difference
        df = time_normalization(df)
        differences.append(compute_td(df, 0, first_chaos_events[i][0]))
    
    min_diff = min(differences)
    
    # Allign the dataframes
    alligned_dataframes = []
    for i, df in enumerate(dataframes):
        # Drop all columns, so that the time difference between the first chaos event
        # first_chaos_events[i][0] and the first time value is min_diff
        df_time_diff = compute_td(df, 0, first_chaos_events[i][0])
        
        # start iterating from the first chaos event to the start of the df
        start_index = first_chaos_events[i][0]
        while df_time_diff > min_diff:
            start_index -= 1
            df_time_diff = compute_td(df, 0, start_index)
        
        # Append the alligned dataframe
        alligned_dataframes.append(df.iloc[start_index:])

    return alligned_dataframes, chaos_events_list

def compute_td(df: pd.DataFrame, start:int, end:int, col: str ="Time",)-> float:
    """
    This helper function computes the difference between the unix timestamps of two indecies in a dataframe
    """
    td = df[col].iloc[end] - df[col].iloc[start]
    return td
    
def get_average_chaos_event_durations(dataframes : list[pd.DataFrame], chaos_events_list : list[list[int,int]]) -> float:
    """
    This function calculates the average duration of all chaos events from the dataframes
    
    Parameters:
    dataframes: list[pd.DataFrame]: list of pandas dataframes
    chaos_events_list: list[list[int,int]]: list lists of chaos events [start, end] indices
    
    Returns:
    average_duration: float: The average duration of all chaos events from the dfs
    """
    average_duration = 0.0
    average_duration_per_df = []

    # iterate over dfs and corresponding events in chaos_events_list
    for df, chaos_events in zip(dataframes, chaos_events_list):
        temp = []
        for chaos_event in chaos_events:
            temp.append(get_duration(df, chaos_event))
        if len(temp) > 0:
            average_duration_per_df.append(sum(temp) / len(temp))

    if len(average_duration_per_df) > 0:
        average_duration = sum(average_duration_per_df) / len(average_duration_per_df)

    return average_duration

        

def average_df(dataframes: list[pd.DataFrame]) -> pd.DataFrame:
    """
    This function averages the value column of all dataframes
    it returns a new dataframe with the average value and the time column of the longest df
    
    Assumption: The df's have been alligned at the start usign the allign_chaos_events method.
    
    Note: There is a small methodical error, which comes from the fact, that re-creating chaos events needs time.
    This takes between 0.5 and 1.5 seconds - very dependent on the system. We cannot account for this in the data.
    
    Parameters:
    dataframes: list[pd.DataFrame]: A list of pandas dataframes
    
    Returns:
    df: pd.DataFrame: The average of all dataframes
    """
    # Find the longest dataframe
    longest_df = max(dataframes, key=lambda x: len(x))
    result_df = pd.DataFrame(longest_df['Time'])
    result_df['Value'] = 0.0

    for i in range(len(longest_df)):
        # for averaging
        value_sum = 0.0
        num_df_with_value = 0

        for df in dataframes:
            #  Check if we may access the value
            if i < len(df) and pd.notna(df.iloc[i]['Value']):
                # Accumulate the values
                value_sum += df.iloc[i]['Value']
                num_df_with_value += 1
        
        # Compute the average value if there were valid entries
        if num_df_with_value > 0:
            result_df.at[i, 'Value'] = value_sum / num_df_with_value
            
    return result_df
        
        
def identify_chaos_around_maxima(df: pd.DataFrame, column: str, median_fraction: float = 1, prominence: float = 1, num_peaks: int = None) -> pd.DataFrame:
    """
    Identifes chaos events based on local maxima in the data. The number of maxima to find can be specified or left empty.
    The maxima are found using the scipy.signal.find_peaks function.
    
    Note: This method ensures that the chaos events are continuous.
    
    Parameters:
    df: pd.DataFrame - A pandas DataFrame containing the data
    column: str - The column name in the DataFrame to analyze for local maxima
    median_fraction: float - The fraction of the median value to use as a threshold (default is 1)
    prominence: float - The prominence for peak detection (default is 1)
    num_peaks: int - The number of peaks to detect (default is None)

    Returns:
    df: pd.DataFrame with a new column 'Chaos' indicating identified chaos events
    """
    
    # Calculate the series median
    median_value = df[column].median()
    
    # Identify peaks (local maxima)
    peaks, _ = find_peaks(df[column].values, prominence=prominence)
                          
    if num_peaks is not None and len(peaks) > num_peaks:
        # select top peaks based on the prominence
        peaks = peaks[np.argsort(df[column].values[peaks])[-num_peaks:]]
    
    # Initialize 'Chaos' column
    df['Chaos'] = 0
    
    for peak in peaks:
        assert type(peak) == np.int64, f"Peak is not an integer: {peak}"
        # Initialize the start and end indices to the peak position
        start = peak
        end = peak
        
        # Iterate outward from the peak to the left
        while start > 0:
            if df.loc[start, column] < median_value * median_fraction:
                    break
            start -= 1
        
        # Iterate outward from the peak to the right
        while end < len(df) - 1:
            if df.loc[end, column] < median_value * median_fraction:
                break
            end += 1

        # Ensure start and end are not the same
        if start == end:
            continue
        
        # mark all point between indices
        df.loc[start:end, 'Chaos'] = 1
                
    return df



# If you want to test the processing code but juypter notebook updates of modules are too infrequent
"""
# Load the dataframes
df_list = []
CURRENT_FOLDER = os.getcwd()
PARENT_FOLDER = os.path.dirname(CURRENT_FOLDER) 
LOG_FOLDER = os.path.join(PARENT_FOLDER, 'experiments', 'runs')
filenames = os.listdir(LOG_FOLDER)
for filename in filenames:
    df_list.append(read_csv(filename))
    
all_chaos_groups = []  

for i, df in enumerate(df_list):
    df = time_normalization(df)
    print(f"Processing {filenames[i]}")
    df = identify_chaos_around_maxima(df, 'Value', num_peaks=3)
    chaos_group_count, chaos_groups = find_number_of_chaos_groups(df)
    all_chaos_groups.append(chaos_groups)
    print(f"chaos groups for {filenames[i]}: {chaos_groups}")

average_duration = get_average_chaos_event_durations([df_list[0]], all_chaos_groups)
print(f"Average duration of chaos events for {filenames[i]}: {average_duration}")
"""