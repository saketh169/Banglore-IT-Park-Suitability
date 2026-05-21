"""
ML-Based Suitability Map - SIMPLIFIED
Generates ONLY: 2 Maps + 2 CSV files
Output: Dashboard/ML_Results folder
"""

import numpy as np
import pandas as pd
import rasterio
import rasterio.transform
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# ==================== PATHS ====================
BASE_PATH = Path(__file__).parent.parent
FINAL_ANALYSIS_PATH = BASE_PATH / "Banglore" / "Final Analysis"
OUTPUT_PATH = Path(__file__).parent / "ML_Results"
OUTPUT_PATH.mkdir(exist_ok=True)

RANDOM_STATE = 42
TRAINING_SAMPLE_SIZE = 1.0  # Use 100% of valid pixels
TEST_SIZE = 0.25
ML_OUTPUT_CLASSES = 5

FEATURE_WEIGHTS = {
    'accessibility': 0.25,
    'business': 0.30,
    'physical': 0.15,
    'infrastructure': 0.15,
    'environmental': 0.15
}

print(f"Output Directory: {OUTPUT_PATH}\n")

# ==================== LOAD FEATURES ====================
print("Loading feature maps...")
feature_files = {
    'accessibility': 'reclass_accessibility.tif',
    'business': 'reclass_business.tif',
    'physical': 'reclass_physical.tif',
    'infrastructure': 'reclass_infrastructure.tif',
    'environmental': 'reclass_environment.tif'
}

features = {}
for feature_name, filename in feature_files.items():
    filepath = FINAL_ANALYSIS_PATH / filename
    with rasterio.open(filepath) as src:
        features[feature_name] = src.read(1).astype(float)

# Normalize dimensions
shapes = {name: data.shape for name, data in features.items()}
max_height = max(shape[0] for shape in shapes.values())
max_width = max(shape[1] for shape in shapes.values())
target_shape = (max_height, max_width)

from rasterio.warp import reproject, Resampling as RasterioResampling
normalized_features = {}
for feature_name, feature_data in features.items():
    if feature_data.shape != target_shape:
        src_transform = rasterio.transform.from_bounds(0, 0, feature_data.shape[1], feature_data.shape[0], 
                                                        feature_data.shape[1], feature_data.shape[0])
        dst_transform = rasterio.transform.from_bounds(0, 0, target_shape[1], target_shape[0], 
                                                        target_shape[1], target_shape[0])
        resampled = np.zeros(target_shape, dtype=np.float32)
        reproject(feature_data, resampled, src_transform=src_transform, src_crs='EPSG:32643',
                  dst_transform=dst_transform, dst_crs='EPSG:32643', resampling=RasterioResampling.bilinear)
        normalized_features[feature_name] = resampled
    else:
        normalized_features[feature_name] = feature_data

features = normalized_features
height, width = target_shape

# ==================== WEIGHTED OVERLAY ====================
print("Computing weighted overlay...")
weighted_overlay = np.zeros((height, width), dtype=float)
for feature_name, feature_data in features.items():
    feature_clean = np.nan_to_num(feature_data, nan=0.0)
    weighted_overlay += feature_clean * FEATURE_WEIGHTS[feature_name]

# Load constraint mask BEFORE saving
constraint_path = FINAL_ANALYSIS_PATH / "constraint_mask.tif"
with rasterio.open(constraint_path) as src:
    constraint_mask = src.read(1).astype(float)

# Apply constraint mask to weighted overlay
restricted_mask = constraint_mask < 0.5
weighted_overlay_masked = weighted_overlay.copy()
weighted_overlay_masked[restricted_mask] = 0

# Save MASKED weighted overlay
weighted_overlay_path = OUTPUT_PATH / "weighted_overlay_suitability.tif"
with rasterio.open(weighted_overlay_path, 'w', driver='GTiff', height=height, width=width, count=1, dtype=rasterio.float32) as dst:
    dst.write(weighted_overlay_masked.astype(rasterio.float32), 1)
print(f"✓ Saved: weighted_overlay_suitability.tif (with mask applied)")

# ==================== PREPARE TRAINING DATA ====================
print("Preparing training data...")
X = np.zeros((height, width, len(features)), dtype=float)
for i, (feature_name, feature_data) in enumerate(features.items()):
    X[:, :, i] = np.nan_to_num(feature_data, nan=0.0)

# Create labels from MASKED weighted overlay
weighted_for_labels = weighted_overlay_masked.copy()
weighted_overlay_valid = weighted_for_labels[weighted_for_labels > 0]  # Only non-zero values
quantiles = [0, 20, 40, 60, 80, 100]
q_values = np.percentile(weighted_overlay_valid, quantiles)

labels = np.zeros((height, width), dtype=int)
for i in range(len(q_values)-1):
    mask = (weighted_for_labels >= q_values[i]) & (weighted_for_labels < q_values[i+1])
    labels[mask] = i + 1
labels[weighted_for_labels >= q_values[-2]] = 5

labels[restricted_mask] = 0

# Extract training samples
valid_mask = labels > 0
valid_indices = np.where(valid_mask)
n_samples = int(TRAINING_SAMPLE_SIZE * len(valid_indices[0]))
sample_indices = np.random.RandomState(RANDOM_STATE).choice(
    len(valid_indices[0]), size=min(n_samples, len(valid_indices[0])), replace=False
)

train_y_indices = (valid_indices[0][sample_indices], valid_indices[1][sample_indices])
train_X = X[train_y_indices]
train_y = labels[train_y_indices]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    train_X, train_y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=train_y
)

# ==================== TRAIN MODEL ====================
print("Training Random Forest...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

rf_model = RandomForestClassifier(
    n_estimators=100, max_depth=20, min_samples_split=10, min_samples_leaf=5,
    random_state=RANDOM_STATE, n_jobs=-1, verbose=0
)
rf_model.fit(X_train_scaled, y_train)

# ==================== PREDICT ====================
print("Generating predictions...")
ml_predictions = np.zeros((height, width), dtype=int)

chunk_size = 100
for i in range(0, height, chunk_size):
    end_i = min(i + chunk_size, height)
    chunk_X = X[i:end_i, :, :]
    chunk_X_reshaped = chunk_X.reshape(-1, chunk_X.shape[-1])
    chunk_X_reshaped = np.nan_to_num(chunk_X_reshaped, nan=0.0)
    chunk_X_scaled = scaler.transform(chunk_X_reshaped)
    chunk_pred = rf_model.predict(chunk_X_scaled)
    ml_predictions[i:end_i, :] = chunk_pred.reshape(end_i-i, width)

ml_predictions[restricted_mask] = 0

# Save ML predictions
ml_pred_path = OUTPUT_PATH / "ml_classifier_predictions.tif"
with rasterio.open(ml_pred_path, 'w', driver='GTiff', height=height, width=width, count=1, dtype=rasterio.uint8) as dst:
    dst.write(ml_predictions.astype(rasterio.uint8), 1)
print(f"✓ Saved: ml_classifier_predictions.tif")

# ==================== SAVE CSV FILES ====================
print("Saving training and test datasets...")

# Training set
train_data = []
for idx, (sample_X, sample_y) in enumerate(zip(X_train, y_train)):
    train_data.append({
        'Sample_ID': idx + 1,
        'Accessibility': sample_X[0],
        'Business': sample_X[1],
        'Physical': sample_X[2],
        'Infrastructure': sample_X[3],
        'Environmental': sample_X[4],
        'True_Class': sample_y,
        'Set': 'Train'
    })

train_df = pd.DataFrame(train_data)
train_csv_path = OUTPUT_PATH / "training_set.csv"
train_df.to_csv(train_csv_path, index=False)
print(f"✓ Saved: training_set.csv ({len(train_df)} samples)")

# Test set
test_data = []
y_pred_test = rf_model.predict(X_test_scaled)
for idx, (sample_X, sample_y, pred_y) in enumerate(zip(X_test, y_test, y_pred_test)):
    test_data.append({
        'Sample_ID': len(train_df) + idx + 1,
        'Accessibility': sample_X[0],
        'Business': sample_X[1],
        'Physical': sample_X[2],
        'Infrastructure': sample_X[3],
        'Environmental': sample_X[4],
        'True_Class': sample_y,
        'Predicted_Class': pred_y,
        'Correct': 1 if sample_y == pred_y else 0,
        'Set': 'Test'
    })

test_df = pd.DataFrame(test_data)
test_csv_path = OUTPUT_PATH / "test_set.csv"
test_df.to_csv(test_csv_path, index=False)
print(f"✓ Saved: test_set.csv ({len(test_df)} samples)")

# ==================== SAVE TRAINED MODEL ====================
print("Saving trained model...")
import pickle

# Save the trained Random Forest model
model_path = OUTPUT_PATH / "trained_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(rf_model, f)
print(f"✓ Saved: trained_model.pkl")

# Save the scaler for preprocessing
scaler_path = OUTPUT_PATH / "scaler.pkl"
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"✓ Saved: scaler.pkl")

print("\n" + "="*60)
print("ALL FILES SAVED TO DASHBOARD FOLDER!")
print("="*60)
print(f"\nLocation: {OUTPUT_PATH}")
print("\nFiles:")
print(f"  1. weighted_overlay_suitability.tif")
print(f"  2. ml_classifier_predictions.tif")
print(f"  3. training_set.csv")
print(f"  4. test_set.csv")
print(f"\nTest Accuracy: {(y_pred_test == y_test).mean():.2%}")
