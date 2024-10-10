# Objective

Develop a Streamlit application for analyzing batch feeding data from confinement lots. The program should generate histograms and statistical tables based on Excel file input. It must be efficient, well-documented, and adhere to Python best practices.

## Program Structure

1. File Upload and Configuration
2. Data Processing and Cleaning
3. Statistical Analysis
4. Results Visualization
5. Statistics Table
6. Data Export

## Required Libraries and Configuration

### Libraries

Include the following import statements at the beginning of your script:

```python
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator, FuncFormatter
import datetime
import io
import base64
import pytz
```

### Streamlit Configuration

Set the page configuration at the beginning of your script:

```python
st.set_page_config(page_title="Data Analysis - Histogram", layout="wide")
```

### Virtual Environment

It's recommended to use a virtual environment. Create and activate it using:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### Requirements File

Create a `requirements.txt` file with the following content:

```
streamlit==1.28.0
pandas==2.1.1
numpy==1.26.0
matplotlib==3.8.0
openpyxl==3.1.2
pytz==2023.3.post1
```

Install the requirements using:

```bash
pip install -r requirements.txt
```

## Detailed Instructions

### 1. File Upload and User Interface

- Use Streamlit to create an intuitive interface with two columns:
  - Left column (`col1`): File upload and parameter selection
  - Right column (`col2`): Results display
- Implement:
  - File uploader for Excel files
  - Date range selector
  - Multi-select dropdowns for operators, food types, and diets (alphabetically ordered, with "All" as default)
  - Checkbox for outlier removal in histogram
  - "Generate" button to initiate analysis

### 2. Data Processing and Cleaning

- Implement `load_and_process_data()`:
  - Read Excel file, skipping first two rows and empty first column
  - Clean and prepare data (e.g., convert "DIFERENÇA (%)" to numeric, handle missing values)
- Implement `filter_data()` to apply user-selected filters
- Handle date conversion using `pd.to_datetime()`
- Calculate and remove outliers using IQR method

### 3. Statistical Analysis

- Implement `calculate_statistics_with_without_outliers()`:
  - Calculate mean and median (with and without outliers)
  - Count batches in difference ranges: 3-5%, 5-7%, >7%
  - Calculate percentages for each range
- Ensure all calculations respect user-selected filters

### 4. Results Visualization

- Implement `create_histogram()`:
  - Use grayscale for bins, darkening away from center (0)
  - Add vertical green line at x=0
  - Customize x-axis labels (color-coded, size-varied)
  - Include informative title
  - Add footer with analysis period, total batches, and generation timestamp (Brasília time)
- Render histogram using `st.pyplot()`

### 5. Statistics Table

- Create a DataFrame for organized statistics display
- Use `styled_stats_df` for table styling (alignment, font size, column width)
- Display table using `st.write()` with `to_html()`

### 6. Data Export

- Implement `save_histogram_as_image()` for PNG download
- Implement `save_statistics_as_csv()` for CSV download
- Provide download links for both

## General Considerations

- Use Brasília timezone for all date/time operations
- Implement robust error handling and input validation
- Set appropriate data types for columns (e.g., dates, numeric values)

## Best Practices and Optimizations

- Use docstrings for all main functions
- Implement comprehensive error handling
- Optimize for large datasets (consider sampling or batch processing)
- Implement caching for repetitive operations
- Follow DRY (Don't Repeat Yourself) principles

## Testing and Validation

- Implement unit tests for critical functions
- Add input validations to ensure data consistency

## Versioning and Documentation

- Maintain an updated README.md
- Use meaningful comments in code
- Keep requirements.txt updated

## Running the Application

To run the Streamlit app, use the following command:

```bash
streamlit run batidas.py
```

## GitHub Commands

```bash
git status
git add batidas.py "instructions_for_app_batidas.md" "requirements.txt" "pseudocode.md"
git commit -m "Updated version of batidas app - improvements in graph and statistics table"
git push origin main
```

## Virtual Environment Activation

```bash
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Remember to deactivate the virtual environment when you're done:

```bash
deactivate
```