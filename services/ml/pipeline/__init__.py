"""CarbonScan AI ML Pipeline.

8 steps from raw point cloud to carbon estimation:
1. Ground classification (CSF)
2. Height normalization (DTM subtraction)
3. Canopy Height Model (pit-free)
4. Individual Tree Detection (Watershed)
5. Wood-Leaf Semantic Segmentation (PointNet++)
6. Quantitative Structure Model (cylinder fitting)
7. Species classification (ResNet on RGB)
8. Allometric carbon calculation (TGO formulas)

See docs/ml/PIPELINE.md for details.
"""

__version__ = "0.1.0"
