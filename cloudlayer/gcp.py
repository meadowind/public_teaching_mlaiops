"""GCP adapter. Implement upload/download/push_image for Lab 1.

SDK:  pip install google-cloud-storage google-cloud-aiplatform
Docs: storage.Client for GCS; Artifact Registry push goes through `docker push` after
      `gcloud auth configure-docker <region>-docker.pkg.dev`.

Hints for Lab 1:
  * BLOB_URI looks like gs://bucket/prefix — parse it here, never in src/.
  * Artifact Registry paths are region-scoped:
        <region>-docker.pkg.dev/<project>/<repo>/<image>
    A common first failure is pushing to gcr.io out of habit; it is a different service.
  * push_image must return the digest reference, not the tag.
  * GCP calls them labels, not tags, and they must be lowercase with no spaces.
    cfg.tags(1) already satisfies that constraint — do not "improve" the values.
"""
from __future__ import annotations

from typing import Any

from cloudlayer.base import CloudAdapter


class GcpAdapter(CloudAdapter):
    def upload(self, local_path: str, key: str) -> str:
        raise NotImplementedError("TODO Lab 1: blob.upload_from_filename, return the gs:// URI")

    def download(self, uri: str, local_path: str) -> None:
        raise NotImplementedError("TODO Lab 1: blob.download_to_filename, creating parents")

    def push_image(self, local_tag: str) -> str:
        raise NotImplementedError("TODO Lab 1: configure-docker, push, return repo@sha256:...")

    # submit_training / register_model  -> Lab 2 (Vertex custom training + Model Registry)
    from __future__ import annotations
import os # 新增這行
from typing import Any
from google.cloud import aiplatform # 新增這行

from cloudlayer.base import CloudAdapter

class GcpAdapter(CloudAdapter):
    # ... (保留你 Lab 1 寫好的 upload, download, push_image) ...

    def submit_training(self, image_uri: str, args: list) -> str:
        # 從環境變數讀取 GCP 設定
        PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
        REGION = os.environ.get("GCP_REGION")
        SERVICE_ACCOUNT = os.environ.get("GCP_SERVICE_ACCOUNT")
        BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME")

        if not all([PROJECT_ID, REGION, SERVICE_ACCOUNT]):
            raise ValueError("Missing GCP environment variables. Check cloud.env.")

        aiplatform.init(project=PROJECT_ID, location=REGION)
        staging_bucket = f"gs://{BUCKET_NAME}/staging"
        
        print(f"Submitting job with image: {image_uri}")
        print(f"Using service account: {SERVICE_ACCOUNT}")

        # 使用底層 CustomJob 控制 Vertex AI 訓練規格
        job = aiplatform.CustomJob(
            display_name="lab2-hyperparameter-tuning",
            staging_bucket=staging_bucket,
            worker_pool_specs=[{
                "machine_spec": {
                    "machine_type": "e2-standard-4" 
                },
                "replica_count": 1,
                "container_spec": {
                    "image_uri": image_uri,
                    "command": ["python", "src/tune.py"] + args
                }
            }]
        )
        
        # 綁定 Run-time identity 並送出工作
        job.submit(service_account=SERVICE_ACCOUNT)
        return job.resource_name

    def wait_training(self, job_id: str) -> None:
        job = aiplatform.CustomJob.get(job_id)
        print(f"Waiting for GCP job to complete: {job_id}")
        
        try:
            job.wait()
            print("Job completed successfully!")
        except Exception as e:
            print(f"Job failed: {e}")
            raise
        
    # deploy / invoke                   -> Lab 3 (Vertex Endpoint)
    # emit_metric                       -> Lab 4 (Cloud Monitoring time series)
    # generate                          -> Lab 5 (managed LLM endpoint; read usageMetadata for tokens)
    # teardown                          -> Lab 5 (filter resources by label)
