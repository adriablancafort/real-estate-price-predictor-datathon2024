import pandas as pd
import numpy as np
import os
import ast
from pathlib import Path
import pickle

def save_dictionary(path, data):
    if not isinstance(data, dict):
        raise ValueError("The data to be saved must be a dictionary.")

    try:
        with open(path, 'wb') as file:
            pickle.dump(data, file)
    except Exception as e:
        raise Exception(f"An error occurred while saving the dictionary: {e}")

def string_to_list(input_string):
    """Converts a string representation of a list into an actual list."""
    if isinstance(input_string, str):
        try:
            return ast.literal_eval(input_string)
        except (ValueError, SyntaxError):
            return []
    return input_string


def string_list_2(value):
    if pd.isna(value):
        return np.nan
    elif isinstance(value, str):
        return [value]
    else:
        return value
    

def one_hot_from_list(df, column_name,dic):
    """Creates one-hot encoding for elements in a column of lists."""
    # Ensure all values in the column are lists
    df[column_name] = df[column_name].apply(lambda x: x if isinstance(x, list) else [])
    # Extract unique elements across all lists
    unique_elements = set(element for lst in df[column_name] for element in lst)
    dic[column_name] = unique_elements
    # Create one-hot encoded columns
    for element in unique_elements:
        new_el = element.replace(" ", "_")
        one_hot_col_name = f"one_hot_{new_el}"
        df[one_hot_col_name] = df[column_name].apply(lambda lst: 1 if element in lst else 0)
    
    return df

def save_dataset(df, filename):
    """Saves the DataFrame to a CSV file."""
    try:
        df.to_csv(filename, index=False)
        print(f"Dataset saved to {filename}")
    except Exception as e:
        print(f"Error saving dataset to {filename}: {e}")

def preprocess_dataframe(df, config):
    """Preprocess the DataFrame by applying one-hot encoding."""
    for col in config['prepare']:
        df[col] = df[col].apply(string_list_2)
    dic = dict()
    for col in config['columns_to_one_hot']:
        if col in df.columns:
            # Convert string representations of lists to actual lists
            df[col] = df[col].apply(string_to_list)
            # Apply one-hot encoding
            df = one_hot_from_list(df, col,dic)
            # Drop the original column
            df.drop(columns=col, inplace=True, errors='ignore')
        else:
            print(f"Column '{col}' not found in DataFrame. Skipping...")
    save_dictionary("../backend/data/saved_data.pkl",dic)
    return df

def encode(data, col, max_val):
    data[col + '_sin'] = np.sin(2 * np.pi * data[col]/max_val)
    data[col + '_cos'] = np.cos(2 * np.pi * data[col]/max_val)
    return data

def main():
    """Main execution function."""
    
    # Define file paths
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
    test_file = os.path.join(parent_dir, 'test_imputed.csv')
    train_file = os.path.join(parent_dir, 'train_imputed.csv')

    # Load datasets
    df_test = pd.read_csv(test_file, sep=',', low_memory=False)
    df_train = pd.read_csv(train_file, sep=',', low_memory=False)
    train_size = len(df_train)
    test_size = len(df_test)
    # Config for preprocessing
    config = {
        'prepare':["Tax.Zoning","Property.PropertyType"],
        'columns_to_one_hot': ["Characteristics.LotFeatures","Structure.Cooling","Tax.Zoning","Property.PropertyType","ImageData.features_reso.results","ImageData.room_type_reso.results"]
    }
    df_combined = pd.concat([df_train, df_test], axis=0, ignore_index=True)
    # Preprocess and save datasets
    # Ensure 'month' is the numeric month value
    df_combined = preprocess_dataframe(df_combined,config)
    df_combined['Listing.Dates.CloseDate'] = pd.to_datetime(df_combined['Listing.Dates.CloseDate'], errors='coerce')

# Extract month and encode it
    df_combined['month'] = df_combined['Listing.Dates.CloseDate'].dt.month
    df_combined = encode(df_combined, 'month', 12)

    # Extract day and encode it
    df_combined['day'] = df_combined['Listing.Dates.CloseDate'].dt.day
    df_combined = encode(df_combined, 'day', 31)
    df_combined.drop(columns=['month','day'],inplace=True, errors='ignore')
    
    df_train = df_combined.iloc[:train_size, :].reset_index(drop=True)
    df_test = df_combined.iloc[train_size:, :].reset_index(drop=True)
    print(list(df_train.columns))
    print(len(df_test.columns))



    save_dataset(df_train, os.path.join(parent_dir, 'df_train.csv'))
    save_dataset(df_test, os.path.join(parent_dir, 'df_test.csv'))


if __name__ == "__main__":
    main()
