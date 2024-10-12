# Documentation for `requirements.txt`

This file lists the Python libraries and their versions required to run the **Batch Data Analysis Application** using Streamlit. Each library serves a specific purpose in the data processing, visualization, or user interface of the application.

## Dependencies:

1. **streamlit>=1.31.0**
   - **Purpose**: Streamlit is used to create the web-based user interface for the application.
   - **Functionality**: It enables file uploads, sliders for adjusting parameters, buttons for actions (like generating histograms), and displaying plots, tables, and download links.

2. **pandas>=2.0.0**
   - **Purpose**: Pandas is the core library for data manipulation and analysis.
   - **Functionality**: It is used for loading and processing Excel files, filtering data, handling DataFrames, and performing operations like grouping and aggregation (e.g., weighted average calculation).

3. **numpy>=1.24.0**
   - **Purpose**: NumPy provides numerical computing capabilities.
   - **Functionality**: It is used for efficient numerical operations, including working with arrays, calculating statistics, and supporting Pandas operations.

4. **matplotlib>=3.7.0**
   - **Purpose**: Matplotlib is a plotting library.
   - **Functionality**: It is used to create histograms and other visualizations within the Streamlit application, allowing for customizations like grid styles, color thresholds, and vertical reference lines.

5. **openpyxl>=3.0.0**
   - **Purpose**: Openpyxl is used for reading Excel files in `.xlsx` format.
   - **Functionality**: This library allows the application to load and process user-uploaded Excel files, which contain the batch data for analysis.

6. **pytz>=2022.1**
   - **Purpose**: Pytz is used for accurate timezone management.
   - **Functionality**: It ensures that all timestamps in the application (e.g., file generation times and footer information in visualizations) adhere to the specified timezone, which is configured as `America/Sao_Paulo` in the application.

7. **PyYAML>=5.4.1**
   - **Purpose**: PyYAML is a library for parsing YAML configuration files.
   - **Functionality**: The application uses this library to load configurations from the `config.yaml` file, which defines settings like column mappings, weights, visualization options, and user interface labels.

## Notes:
- The version constraints (`>=`) ensure that the program uses versions of these libraries that contain the necessary features and improvements while allowing flexibility for newer versions.
- It is important to install these dependencies in a virtual environment to avoid conflicts with other Python projects.
