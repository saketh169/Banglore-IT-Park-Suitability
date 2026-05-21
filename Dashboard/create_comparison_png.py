"""
Create Comparison: Weighted Overlay vs ML Predictions
"""

import numpy as np
import rasterio
from pathlib import Path
import matplotlib.pyplot as plt

# Paths
RESULTS_PATH = Path(__file__).parent / "ML_Results"

# Load maps
with rasterio.open(RESULTS_PATH / "weighted_overlay_suitability.tif") as src:
    weighted = src.read(1)

with rasterio.open(RESULTS_PATH / "ml_classifier_predictions.tif") as src:
    ml_pred = src.read(1)

# Create side-by-side comparison figure
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Plot 1: Weighted Overlay (Final)
weighted_display = weighted.astype(float)
im1 = axes[0].imshow(weighted_display, cmap='turbo', vmin=0, vmax=5)
axes[0].set_title('Final Weighted Overlay Suitability Map\n(WITH CONSTRAINT MASK APPLIED)', fontweight='bold', fontsize=14, color='darkgreen')
axes[0].set_xlabel('X (pixels)', fontsize=11)
axes[0].set_ylabel('Y (pixels)', fontsize=11)
axes[0].grid(alpha=0.2, linestyle='--')
cbar1 = plt.colorbar(im1, ax=axes[0], label='Suitability Score (1-5)')

# Plot 2: ML Predictions
ml_display = ml_pred.astype(float)
im2 = axes[1].imshow(ml_display, cmap='turbo', vmin=0, vmax=5)
axes[1].set_title('ML Classifier Predictions\n(WITH CONSTRAINT MASK APPLIED)', fontweight='bold', fontsize=14, color='darkgreen')
axes[1].set_xlabel('X (pixels)', fontsize=11)
axes[1].set_ylabel('Y (pixels)', fontsize=11)
axes[1].grid(alpha=0.2, linestyle='--')
cbar2 = plt.colorbar(im2, ax=axes[1], label='Predicted Class (1-5)')

plt.suptitle('Comparison: Final Weighted Overlay vs ML Predictions\n(Both with Constraint Mask Applied)', fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()

# Save as single comparison PNG
output_path = RESULTS_PATH / "comparison_final_vs_predicted.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✓ Saved: comparison_final_vs_predicted.png")
print(f"  Location: {output_path}")
plt.close()

print("\n✅ Comparison image created successfully!")
