# MediFusion deployment runbook

MediFusion's chest X-ray feature is an experimental, research-only
clinician-review flag. It is not a diagnostic or treatment service. Do not
upload real patient data while validating this deployment.

## Free Render + private GitHub release

The approved checkpoint is intentionally excluded from Git:

`backend/model_artifacts/medifusion_densenet_full_best.pt`

It must be kept private. Do not commit it to Git or put it in a public URL.

1. Create a separate **private** GitHub repository for model artifacts (for
   example, `medifusion-model-artifacts`). Do not use the public
   `medifusion-connected` application repository.
2. Create a private GitHub Release in that artifact repository (for example,
   tag `model-v1`) and upload `medifusion_densenet_full_best.pt` as its
   release asset.
3. Copy that asset's browser download URL.
4. Create a fine-grained GitHub personal access token limited only to the
   private artifact repository with **Contents: Read-only** permission. Never
   paste it into this repository or frontend code.

## Render setup

The existing Render service is on the free plan. Its filesystem is erased when
it restarts, so the startup command downloads the private model release again
when needed. This is suitable for a demo, but makes cold starts slower.

In Render, open **medifusion-api** > **Environment** and add these values:

   ```text
   MEDIFUSION_XRAY_MODEL_ENABLED=1
   MEDIFUSION_MODEL_RELEASE_URL=<private GitHub release asset URL>
   MEDIFUSION_MODEL_GITHUB_TOKEN=<read-only GitHub token>
   ```

The checkpoint hash is already set by `render.yaml`. Redeploy after adding
the values.

The `render.yaml` configuration generates `SECRET_KEY`, runs in production
mode, and limits browser origins to the Vercel deployment.

Uploaded DICOMs and lab reports remain temporary on the Render free plan.
Use only non-sensitive demonstration files until separate private object
storage is configured for uploads.

## Production controls still required

Before handling any real patient data, configure private encrypted object
storage for uploads, a managed Redis service, and an identity-provisioning
process for clinicians and lab technicians. The production configuration only
allows patient self-registration; staff accounts must not be created through
the public sign-up page. Use a managed secrets store and rotate `SECRET_KEY`
and the GitHub access token on a documented schedule.

The API provides a `/health` endpoint, but it does not replace operational
monitoring. Add uptime checks, centralized structured logs, error tracking,
database backups and restore testing, and alerting before a production launch.
Do not use the current Render free-plan deployment for protected health data.

## Verification

After deployment, verify these URLs:

```text
https://medifusion-api-11yd.onrender.com/health
https://medifusion-api-11yd.onrender.com/predict/xray-model-status
```

The model endpoint must return `ready: true`, `enabled: true`, and
`checkpoint_present: true`. Then complete an end-to-end test using a
non-sensitive test DICOM and confirm the patient and doctor workflows.
