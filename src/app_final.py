import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import logging
import webbrowser

# Set up logging to track progress and errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LaptopPredictor:
    """
    A class responsible for loading, cleaning, training, and predicting laptop data.
    This class contains all the machine learning logic and data preprocessing.
    """
    def __init__(self):
        self.models = {}  # To store trained models for different targets (Price, RAM, etc.)
        self.scaler = StandardScaler()  # Scaler for normalizing input data
        self.df = None  # Placeholder for the DataFrame containing laptop data

    def clean_storage_value(self, value):
        """
        Converts storage size strings into numeric values in GB.
        Example: '1TB' becomes 1024, '500GB' remains 500.
        """
        try:
            value = str(value).lower()
            if 'tb' in value:
                return float(value.replace('tb', '').strip()) * 1024  # Convert TB to GB
            return float(value.replace('gb', '').strip())
        except (ValueError, AttributeError):
            return None

    def load_and_clean_data(self, file_path):
        """
        Loads the CSV file, cleans the data, and prepares it for training.
        - Extracts numeric values from RAM and Disk Size columns.
        - Filters out invalid or outlier data.
        """
        try:
            # Load data from CSV
            self.df = pd.read_csv(file_path)
            logging.info("Data loaded successfully")

            # Clean and transform data - handle non-string values
            # Convert columns to string type first
            self.df['ram'] = self.df['ram'].astype(str)
            self.df['disk_size'] = self.df['disk_size'].astype(str)
            self.df['rating'] = self.df['rating'].astype(str)
            self.df['price'] = self.df['price'].astype(str)

            # Extract numeric values
            self.df['RAM'] = self.df['ram'].str.extract(r'(\d+)').astype(float)
            self.df['Disk_Size'] = self.df['disk_size'].apply(self.clean_storage_value)
            self.df['Rating'] = pd.to_numeric(self.df['rating'], errors='coerce')
            self.df['Price'] = pd.to_numeric(self.df['price'].str.replace('[$,]', '', regex=True), errors='coerce')

            # Remove invalid rows and outliers
            self.df = self.df[
                (self.df['Price'] > 0) &
                (self.df['RAM'] > 0) &
                (self.df['Disk_Size'] > 0) &
                (self.df['Rating'].between(1, 5))
            ]

            logging.info(f"Data cleaned. Remaining rows: {len(self.df)}")
            return True
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return False

    def train_models(self):
        """
        Trains a Random Forest Regressor for each target column (Price, RAM, etc.).
        Saves the trained models, predictors, RMSE, and R2 scores.
        """
        try:
            features = ['RAM', 'Disk_Size', 'Rating', 'Price']
            for target in features:
                # Define predictors (all features except the target)
                predictors = [f for f in features if f != target]
                X = self.df[predictors]
                y = self.df[target]

                # Scale data using StandardScaler
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42
                )

                # Train a Random Forest model
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)

                # Evaluate the model
                y_pred = model.predict(X_test)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)

                # Store model details
                self.models[target] = {
                    'model': model,
                    'predictors': predictors,
                    'rmse': rmse,
                    'r2': r2,
                    'scaler': scaler  # Save the scaler
                }

                logging.info(f"{target} Model - RMSE: {rmse:.2f}, R2: {r2:.2f}")
        except Exception as e:
            logging.error(f"Error training models: {str(e)}")
            return False
        return True

class PredictorGUI:
    """
    A class responsible for the graphical user interface (GUI) for user interaction.
    """
    def __init__(self, predictor):
        self.predictor = predictor
        self.root = tk.Tk()
        self.root.title("Laptop Predictor")
        self.root.geometry("800x600")
        self.current_link = None
        self.setup_gui()

    def setup_gui(self):
        """Sets up the GUI layout and components."""
        input_frame = ttk.LabelFrame(self.root, text="Input Parameters", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        self.entries = {}
        for i, field in enumerate(['RAM', 'Disk_Size', 'Rating', 'Price']):
            ttk.Label(input_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5)
            self.entries[field] = ttk.Entry(input_frame)
            self.entries[field].grid(row=i, column=1, padx=5, pady=5)

        self.pred_type = ttk.Combobox(input_frame, values=['Price', 'RAM', 'Disk_Size', 'Rating'], state='readonly')
        self.pred_type.set('Price')
        self.pred_type.grid(row=len(self.entries), column=0, columnspan=2, pady=10)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=len(self.entries)+1, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Predict", command=self.predict).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        self.result_frame = ttk.LabelFrame(self.root, text="Results", padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.result_label = ttk.Label(self.result_frame, text="")
        self.result_label.pack()

        self.suggestion_text = tk.Text(self.result_frame, height=10, width=70, cursor="hand2")
        self.suggestion_text.pack(pady=10)
        self.suggestion_text.bind("<Button-1>", self.open_link)

    def predict(self):
        """Handles predictions and displays results."""
        try:
            target = self.pred_type.get()
            inputs = {k: float(v.get()) for k, v in self.entries.items() if v.get()}
            model_info = self.predictor.models[target]
            predictors = model_info['predictors']
            scaler = model_info['scaler']

            input_data = pd.DataFrame([inputs], columns=predictors)  # Add feature names
            input_data = scaler.transform(input_data)
            prediction = model_info['model'].predict(input_data)[0]

            self.result_label.config(
                text=f"Predicted {target}: {prediction:.2f}\n"
                     f"Model R² Score: {model_info['r2']:.2f}\n"
                     f"RMSE: {model_info['rmse']:.2f}"
            )
            self.show_similar_laptops(inputs, target)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def clear_fields(self):
        """Clears all input fields and resets results."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.result_label.config(text="")
        self.suggestion_text.delete(1.0, tk.END)
        self.current_link = None

    def show_similar_laptops(self, inputs, target):
        """Finds and displays the most similar laptop."""
        try:
            df_temp = self.predictor.df.copy()
            predictors = self.predictor.models[target]['predictors']
            df_temp['Similarity'] = df_temp[predictors].sub(pd.Series(inputs)).abs().sum(axis=1)
            similar_laptop = df_temp.nsmallest(1, 'Similarity').iloc[0]
            self.current_link = similar_laptop.get('link', None)
            self.suggestion_text.delete(1.0, tk.END)
            self.suggestion_text.insert(
                tk.END,
                f"Title: {similar_laptop.get('title', 'N/A')}\n"
                f"Price: ${similar_laptop.get('Price', 0):.2f}\n"
                f"Click here to view: {self.current_link if self.current_link else 'N/A'}\n"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error showing suggestions: {str(e)}")

    def open_link(self, event):
        """Opens the link to the suggested laptop in the web browser."""
        if self.current_link:
            webbrowser.open(self.current_link)

def main():
    predictor = LaptopPredictor()
    if predictor.load_and_clean_data("/Users/akshatsharma/Desktop/amazon_project/LapVision/airflow/data/laptop.csv"):
        if predictor.train_models():
            gui = PredictorGUI(predictor)
            gui.root.mainloop()
        else:
            messagebox.showerror("Error", "Failed to train models")
    else:
        messagebox.showerror("Error", "Failed to load data")

if __name__ == "__main__":
    main()
