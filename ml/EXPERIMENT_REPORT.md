# MediFusion chest X-ray triage experiment

**Status:** completed research baseline  
**Intended use:** experimental flag for clinician/radiologist review of a chest X-ray for possible pulmonary opacity.  
**Not intended for:** diagnosis, treatment decisions, autonomous clinical use, or use on people outside a properly approved research workflow.

## Research reference

This experiment uses the RSNA Pneumonia Detection Challenge data derived from the NIH ChestX-ray14 collection. The supporting publication is:

> Shih G, Wu CC, Halabi SS, et al. *Augmenting the National Institutes of Health Chest Radiograph Dataset with Expert Annotations of Possible Pneumonia.* Radiology: Artificial Intelligence. 2019;1(1):e180041. doi:10.1148/ryai.2019180041.

The target label is **possible pulmonary opacity**, not a confirmed pneumonia diagnosis.

## Data and patient-safe split

| Split | Images | Positive | Negative |
| --- | ---: | ---: | ---: |
| Train | 23,748 | 5,686 | 18,062 |
| Validation | 2,968 | 710 | 2,258 |
| Test | 2,968 | 710 | 2,258 |
| Total | 29,684 | 7,106 | 22,578 |

Images were mapped to original NIH patient identifiers before splitting. Each patient was assigned to only one split, preventing known patient overlap across train, validation, and test sets.

## Model and training configuration

| Item | Value |
| --- | --- |
| Architecture | ImageNet-pretrained DenseNet-121 |
| Input | Single DICOM chest X-ray rendered as three 224 x 224 channels |
| Image preparation | Rescale slope/intercept, MONOCHROME1 inversion when needed, 1st-99th percentile normalization |
| Training loss | Weighted binary cross-entropy with positive-class weight 3.177 |
| Optimizer | AdamW, learning rate 0.0001, weight decay 0.0001 |
| Batch size | 32 |
| Full-training epochs | 3 |
| Model-selection measure | Validation AUROC |

The model from **epoch 1** was selected because it achieved the highest validation AUROC. Later epochs reduced validation performance, which is consistent with early overfitting.

## Results

### Pilot experiment

The initial 4,000-image pilot achieved a validation AUROC of 0.7635 and an internal-test AUROC of 0.7663.

### Full-training experiment

| Measure | Result |
| --- | ---: |
| Best validation AUROC (epoch 1) | **0.7959** |
| Internal-test AUROC | **0.7925** |
| Internal-test average precision | **0.5848** |

### Experimental triage threshold

A threshold of **0.360** was selected on the validation split to target at least 90% validation sensitivity. On the internal test split, it produced:

| Measure | Result |
| --- | ---: |
| True positives | 623 |
| True negatives | 1,091 |
| False positives | 1,167 |
| False negatives | 87 |
| Sensitivity | 87.8% |
| Specificity | 48.3% |
| Precision | 34.8% |
| Negative predictive value | 92.6% |

At this research threshold, about 60% of images are flagged for review. This favors finding more potential positive cases but creates many additional review alerts.

## Error analysis

The experimental threshold produced 87 false negatives and 1,167 false positives. Random samples and CSV lists were saved in Google Drive under `medifusion_error_analysis`.

These images must be interpreted by qualified radiologists. Model probability does not explain the underlying image finding and should not be treated as a clinical explanation.

## Important limitations

1. This is a single-dataset internal evaluation, not an external clinical validation.
2. The test split was examined during the pilot experiment, so the reported full-model test result is an internal comparison rather than a strictly blinded confirmatory result.
3. The target is an expert-annotation label for possible pulmonary opacity; it does not establish a pneumonia diagnosis.
4. Performance can differ across scanners, hospitals, patient populations, image quality, and disease prevalence.
5. Predictive values depend on the prevalence in this dataset and cannot be carried directly into clinical practice.
6. A model with 87 false negatives at the chosen threshold must not be used as a stand-alone screening, diagnostic, or treatment system.

## Saved Google Drive artifacts

- `medifusion_densenet_full_best.pt` - selected DenseNet-121 checkpoint
- `medifusion_densenet_full_history.csv` - epoch-by-epoch training history
- `medifusion_full_test_predictions.csv` - per-image internal-test predictions
- `medifusion_full_test_results.txt` - AUROC and default-threshold metrics
- `medifusion_selected_triage_threshold.txt` - validation-selected threshold
- `medifusion_full_triage_threshold_results.txt` - frozen-threshold internal-test metrics
- `medifusion_error_analysis/` - false-positive and false-negative lists and image grids

## Recommended next steps

1. Have a qualified radiologist review representative false-negative and false-positive cases.
2. Evaluate the frozen model and threshold on a genuinely independent external dataset.
3. Add probability calibration and subgroup analysis only with an approved research plan.
4. If integrating into MediFusion, present it only as an **experimental clinician-review flag** with the model version, threshold, and safety limitations visible to the user.
