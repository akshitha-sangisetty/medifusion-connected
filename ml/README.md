# MediFusion ML workspace

This workspace is for research-only development of a clinician-reviewed chest-X-ray triage model. It must not be used to diagnose patients or make treatment decisions.

## Local data locations

- Images: `C:\rsna\mdai_rsna_project_x9N20BZa_images_2018-07-20-153330`
- Annotations: `C:\rsna_annotations\pneumonia-challenge-annotations-adjudicated-kaggle_2018.json`

The source dataset stays outside this Git repository because it is large and governed by its own terms of use.

## First check

After installing the local dependencies, run:

```powershell
& "C:\Users\Akshitha\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\ml\verify_dataset.py
```

## Prepare labels

The first run reads a 500-image sample and writes a local manifest. It uses only
the calculated RSNA labels and gives each patient one deterministic split, which
prevents the same patient appearing in both training and test data.

```powershell
& "C:\Users\Akshitha\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\ml\prepare_manifest.py
```

Run with `--full` only after reviewing the sample report.

## Apply original patient mapping

The RSNA DICOM headers use per-image anonymized identifiers. After downloading
the RSNA-to-NIH mapping file, create the final manifest with original NIH
patient groups before training:

```powershell
& "C:\Users\Akshitha\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\ml\apply_patient_mapping.py
```
